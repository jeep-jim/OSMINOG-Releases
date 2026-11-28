#!/usr/bin/env python3
"""Import the reviewed645 fixture graph without flattening relative imports."""
import base64
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import runpy
import stat
import sys

TOOLS = Path(__file__).resolve().parent
SNAPSHOT = TOOLS / 'mouse645-source'
def need(value, message):
    if not value:
        raise ValueError('Mouse645 source graph: ' + message)


def managed_root(value):
    # The caller approves this directory. System aliases above it (macOS /var
    # and /tmp) are allowed; the managed root itself must be a real directory.
    root = Path(value).absolute()
    info = root.lstat()
    need(stat.S_ISDIR(info.st_mode) and not stat.S_ISLNK(info.st_mode), 'linked or invalid managed root: ' + str(root))
    return root.resolve(strict=True)


def guarded_path(root, name, *, allow_missing=False):
    root = managed_root(root)
    need(isinstance(name, str) and name and '\\' not in name and '\0' not in name, 'invalid relative file path')
    parts = PurePosixPath(name).parts
    need(parts and not PurePosixPath(name).is_absolute() and all(part not in ('', '.', '..') for part in parts),
         'file path escapes its managed root')
    target = root
    for index, part in enumerate(parts):
        target = target / part
        try:
            info = target.lstat()
        except FileNotFoundError:
            need(allow_missing, 'missing managed file: ' + name)
            continue
        need(not stat.S_ISLNK(info.st_mode), 'linked managed path component: ' + str(target))
        need(stat.S_ISDIR(info.st_mode) if index < len(parts) - 1 else stat.S_ISREG(info.st_mode),
             'invalid managed path component: ' + str(target))
    need(target.resolve(strict=not allow_missing).is_relative_to(root), 'resolved file escapes its managed root')
    return target


@contextmanager
def parent_descriptor(root, name, *, create=False):
    # Descriptor-relative opens keep an intervening directory replacement from
    # redirecting a verified read/write through a newly installed child symlink.
    root = managed_root(root)
    guarded_path(root, name, allow_missing=create)
    parts = PurePosixPath(name).parts
    descriptor = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in parts[:-1]:
            if create:
                try:
                    os.mkdir(part, dir_fd=descriptor)
                except FileExistsError:
                    pass
            info = os.stat(part, dir_fd=descriptor, follow_symlinks=False)
            need(stat.S_ISDIR(info.st_mode) and not stat.S_ISLNK(info.st_mode), 'linked managed parent')
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        yield descriptor, parts[-1]
    finally:
        os.close(descriptor)


def read_bytes(root, name, *, limit=8 * 1024**2):
    with parent_descriptor(root, name) as (parent, leaf):
        descriptor = os.open(leaf, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
        with os.fdopen(descriptor, 'rb') as stream:
            info = os.fstat(stream.fileno())
            need(stat.S_ISREG(info.st_mode) and info.st_size <= limit, 'invalid or oversized managed file: ' + name)
            raw = stream.read(limit + 1)
            need(len(raw) <= limit, 'managed file grew beyond its limit: ' + name)
            return raw


def write_bytes(root, name, raw):
    with parent_descriptor(root, name, create=True) as (parent, leaf):
        descriptor = os.open(leaf, os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600, dir_fd=parent)
        with os.fdopen(descriptor, 'wb') as stream:
            need(stat.S_ISREG(os.fstat(stream.fileno()).st_mode), 'invalid managed write target: ' + name)
            stream.truncate(0)
            stream.write(raw)


def remove_file(root, name):
    with parent_descriptor(root, name) as (parent, leaf):
        os.unlink(leaf, dir_fd=parent)


FILES = json.loads(read_bytes(TOOLS, 'mouse645-source-files.json'))
FLAT_HELPERS = tuple(runpy.run_path(str(TOOLS / 'mouse645-current.py'))['HELPERS']) + (
    'mouse-verify.py', 'mouse-631-acceptance.py', 'mouse-update-verify.py',
    'mouse-install-update.cjs', 'mouse-update.cjs', 'legacy629-update.cjs', 'legacy644-update.cjs')


def checked(name):
    need(isinstance(name, str) and name in FILES, 'unreviewed dependency')
    relative = PurePosixPath(name)
    need(not relative.is_absolute() and '..' not in relative.parts and '\\' not in name
         and relative.parts[0] in ('tools', 'desktop', 'services', 'infra', '.github'), 'unsafe source path')
    raw = read_bytes(SNAPSHOT, name, limit=2 * 1024**2)
    need(0 < len(raw) <= 2 * 1024**2 and re.fullmatch('[a-f0-9]{64}', FILES[name])
         and hashlib.sha256(raw).hexdigest() == FILES[name], 'reviewed source bytes changed: ' + name)
    return raw


def validate():
    for name in FILES:
        checked(name)


def fetch(api, source_repo, source, output):
    validate()
    need(source_repo == 'jeep-jim/OSMINOG' and isinstance(source, str)
         and re.fullmatch('[a-f0-9]{40}', source), 'source repository or immutable commit differs')
    output = managed_root(output)
    # Reject a pre-existing child link before even the first import is written.
    for name in FILES:
        guarded_path(output, name, allow_missing=True)
    for name in FLAT_HELPERS:
        guarded_path(output, name)
        guarded_path(output, 'tools/' + name, allow_missing=True)
    for name in FILES:
        record = api(source_repo, f'contents/{name}?ref={source}')
        need(record.get('type') == 'file' and record.get('encoding') == 'base64', 'non-file source response: ' + name)
        raw = base64.b64decode(record['content'], validate=False)
        blob = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
        need(record.get('sha') == blob and raw == checked(name), 'Git blob / reviewed source mismatch: ' + name)
        write_bytes(output, name, raw)
    # Old gates still read their flat source copies. The actual645 driver runs
    # from tools/, where ../desktop and ../services now retain source semantics.
    for name in FLAT_HELPERS:
        raw = read_bytes(output, name)
        target = guarded_path(output, 'tools/' + name, allow_missing=True)
        if target.exists():
            need(read_bytes(output, 'tools/' + name) == raw, 'conflicting helper bytes: ' + name)
        else:
            write_bytes(output, 'tools/' + name, raw)
    verify(output)


def verify(output):
    output = managed_root(output)
    for name in FILES:
        need(read_bytes(output, name) == checked(name),
             'imported source graph changed: ' + name)
    for name in FLAT_HELPERS:
        need(read_bytes(output, 'tools/' + name) == read_bytes(output, name), 'structured legacy helper changed: ' + name)


if __name__ == '__main__':
    if len(sys.argv) != 3 or sys.argv[1] != 'verify':
        raise SystemExit('Expected verify IMPORTED_DIRECTORY')
    verify(Path(sys.argv[2]))
    print('MOUSE_645_STRUCTURED_SOURCE_HELPERS_PASS')
