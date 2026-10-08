"""Prepare a full release from a verified public baseline and a checksum-pinned patch.
The resulting uncompressed file set must equal the already-tested CI package.
This prepares an immutable archive only; the existing publisher advances the feed.
"""
import base64
import gzip
import hashlib
import io
import json
import pathlib
import re
import subprocess
import sys
import tempfile
import urllib.request
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
MAX_PACKAGE = 64 * 1024 * 1024
MAX_CONTENT = 128 * 1024 * 1024
REPO = "jeep-jim/OSMINOG-Releases"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def version(value):
    if not re.fullmatch(r"\d+(?:\.\d+){2,3}", str(value)):
        raise ValueError("Invalid version")
    return str(value)


def safe_path(name):
    path = pathlib.PurePosixPath(name)
    if (not name or "\\" in name or "\x00" in name or path.is_absolute()
            or any(p in ("..", ".git") for p in path.parts)):
        raise ValueError("Unsafe package path")
    return path


def package_files(data):
    if len(data) > MAX_PACKAGE:
        raise ValueError("Oversized package")
    result = {}
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        if len(archive.infolist()) > 10000 or sum(x.file_size for x in archive.infolist()) > MAX_CONTENT:
            raise ValueError("Oversized expanded package")
        for entry in archive.infolist():
            safe_path(entry.filename)
            if entry.is_dir():
                continue
            if (entry.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError("Symlink in package")
            if entry.filename in result:
                raise ValueError("Duplicate package entry")
            result[entry.filename] = archive.read(entry)
    return result


def content_digest(files):
    return sha("".join(name + "\0" + sha(data) + "\n"
                       for name, data in sorted(files.items())).encode("utf-8"))


def build(target):
    target = version(target)
    stage = ROOT / "staging/chrome-extension" / target
    recipe = json.loads((stage / "reconstruct.json").read_text("utf-8"))
    if recipe["schema"] != "osminog-verified-overlay/v1" or recipe["version"] != target:
        raise ValueError("Wrong overlay recipe")
    feed = json.loads((ROOT / "channels/dev/chrome-extension.json").read_text("utf-8"))
    current = feed.get("signed", feed).get("latest", {}).get("version", "0.0.0")
    if tuple(map(int, version(current).split("."))) > tuple(map(int, target.split("."))):
        raise ValueError("Refusing to prepare a version older than the current dev feed")
    base_version = version(recipe["baseVersion"])
    base_dir = ROOT / "platforms/chrome-extension/releases" / base_version
    base_meta = json.loads((base_dir / "release-v2.json").read_text("utf-8"))
    base_name = base_meta["package"]
    if pathlib.PurePosixPath(base_name).name != base_name or not base_name.endswith(".zip"):
        raise ValueError("Invalid base package name")
    if base_meta["sha256"] != recipe["baseSha256"]:
        raise ValueError("Baseline metadata changed")
    base_file = base_dir / base_name
    if base_file.exists():
        baseline = base_file.read_bytes()
    else:
        url = f"https://github.com/{REPO}/releases/download/chrome-v{base_version}/{base_name}"
        with urllib.request.urlopen(url, timeout=60) as response:
            baseline = response.read(MAX_PACKAGE + 1)
    if len(baseline) != base_meta["size"] or sha(baseline) != recipe["baseSha256"]:
        raise ValueError("Baseline byte size / SHA-256 mismatch")
    base_files = package_files(baseline)
    compressed = base64.b64decode("".join((stage / "overlay.patch.gz.b64").read_text("ascii").split()), validate=True)
    with gzip.GzipFile(fileobj=io.BytesIO(compressed)) as stream:
        patch = stream.read(4 * 1024 * 1024 + 1)
    if len(patch) > 4 * 1024 * 1024 or sha(patch) != recipe["patchSha256"]:
        raise ValueError("Overlay patch SHA-256 mismatch")
    for line in patch.decode("utf-8").splitlines():
        if line.startswith(("--- ", "+++ ")):
            name = line[4:].split("\t", 1)[0]
            if name != "/dev/null":
                if not name.startswith(("a/", "b/")):
                    raise ValueError("Invalid patch path prefix")
                safe_path(name[2:])
    with tempfile.TemporaryDirectory(prefix="osminog-release-") as tmp:
        work = pathlib.Path(tmp) / "package"
        work.mkdir()
        for name, data in base_files.items():
            path = work / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        patch_file = pathlib.Path(tmp) / "overlay.patch"
        patch_file.write_bytes(patch)
        subprocess.run(["git", "apply", "--no-index", "--unidiff-zero", str(patch_file)], cwd=work, check=True)
        files = {p.relative_to(work).as_posix(): p.read_bytes() for p in work.rglob("*") if p.is_file()}
        if len(files) != recipe["fileCount"] or content_digest(files) != recipe["contentSha256"]:
            raise ValueError("Reconstructed files do not equal the verified CI build")
        manifest = json.loads(files["manifest.json"])
        base_manifest = json.loads(base_files["manifest.json"])
        if manifest["name"] != "OSMINOG" or manifest["version"] != target:
            raise ValueError("Wrong product / version")
        if manifest.get("key") != base_manifest.get("key") or sha(manifest.get("key", "").encode()) != recipe["fixedIdentitySha256"]:
            raise ValueError("Extension identity changed")
        for key in ("permissions", "host_permissions", "optional_host_permissions", "content_security_policy"):
            if manifest.get(key) != base_manifest.get(key):
                raise ValueError("Overlay unexpectedly changes permissions / security policy")
        metadata = dict(recipe["release"])
        if metadata["version"] != target or metadata["manifestVersion"] != target:
            raise ValueError("Release metadata version mismatch")
        name = metadata["package"]
        if pathlib.PurePosixPath(name).name != name or not name.endswith(".zip"):
            raise ValueError("Invalid output package name")
        build_metadata = json.loads(files["OSMINOG_BUILD.json"])
        if build_metadata["version"] != target or build_metadata["artifact"] != name:
            raise ValueError("Build metadata mismatch")
        for script in ("background.js", "osminog-workdesk.js", "osminog-canvas-ux.js"):
            subprocess.run(["node", "--check", str(work / script)], check=True)
        release_dir = ROOT / "platforms/chrome-extension/releases" / target
        release_dir.mkdir(parents=True, exist_ok=True)
        package = release_dir / name
        if package.exists():
            data = package.read_bytes()
            if package_files(data) != files:
                raise ValueError("Refusing to replace an existing immutable version")
        else:
            output = io.BytesIO()
            with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
                for relative, payload in sorted(files.items()):
                    item = zipfile.ZipInfo(relative, date_time=(1980, 1, 1, 0, 0, 0))
                    item.compress_type = zipfile.ZIP_DEFLATED
                    item.external_attr = 0o100644 << 16
                    archive.writestr(item, payload, compresslevel=9)
            data = output.getvalue()
            if package_files(data) != files:
                raise ValueError("Built archive failed content round trip")
            package.write_bytes(data)
        metadata.update(size=len(data), sha256=sha(data), contentSha256=content_digest(files), fileCount=len(files), runtimeVerified=False)
        (release_dir / "release-v2.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", "utf-8")
        notes = (metadata["notes"] + f"\n\nПакет: `{name}`\nSHA-256: `{sha(data)}`\nРазмер: {len(data)} байт.\n"
                 + f"Проверенная сборка: {metadata['verificationUrl']}\n"
                 + "\nСостав распакованных файлов побайтово совпадает с проверенной CI-сборкой. Проверка установки на компьютере владельца отдельно не выполнялась.\n")
        (release_dir / "README.md").write_text(notes, "utf-8")
        print(json.dumps({"version": target, "package": name, "size": len(data), "sha256": sha(data), "files": len(files)}))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: reconstruct_chrome_overlay.py VERSION")
    build(sys.argv[1])
