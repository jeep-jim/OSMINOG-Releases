#!/usr/bin/env python3
"""Select a single635 publisher; unready sibling platforms never get a job."""
from contextlib import redirect_stdout
import json
from pathlib import Path
import runpy
import sys

ROOT=Path(__file__).resolve().parents[1]
PLATFORMS={
 'macos-arm64':('6.0.35-arm64','mouse635-release.py','validate','Mouse Browser 6.0.35: publish pinned source and verified Mac packages'),
 'windows-x64':('6.0.35-windows-x64','mouse635-windows-release.py','pin','Publish verified Mouse Browser 6.0.35 Windows x64'),
 'linux-x64':('6.0.35-linux-x64','mouse635-linux-release.py','pin','Publish verified Mouse Browser 6.0.35 Linux x64'),
}
CLAIMS=('source','sourceMerge','sourcePR','run','artifact','verificationArtifact','sourceAttempt','sourceJob','attempt','job','archiveSHA256','artifactSHA256','verificationSHA256')


def publication_ready(platform,*,root=ROOT,load=runpy.run_path):
 if platform not in PLATFORMS:raise ValueError('Unknown635 publication platform')
 folder,module,entry,trigger=PLATFORMS[platform]
 stage=root/'staging/mouse'/folder;pin=json.loads((stage/'pin.json').read_text());owner=stage/'PUBLISH_OWNER'
 if pin.get('version')!='6.0.35' or type(pin.get('ready')) is not bool:raise ValueError('Invalid platform pin version/readiness')
 if pin['ready'] is False:
  if owner.exists():raise ValueError('Unready platform has a publication trigger')
  if any(pin.get(key) is not None for key in CLAIMS):raise ValueError('Unready platform contains provenance claims')
  packages=pin.get('packages')
  if not isinstance(packages,dict):
   package=pin.get('package');packages={'installer':package} if isinstance(package,dict) else {}
  if not packages or any(not isinstance(value,dict) or value.get('size') is not None or value.get('sha256') is not None for value in packages.values()):raise ValueError('Unready platform contains package claims')
  return False
 if not owner.is_file() or owner.is_symlink() or owner.read_text().strip()!=trigger:raise ValueError('Ready platform lacks its exact owner publication trigger')
 # Existing full provenance checks precede the eligible-runner output.
 # Import and fresh installed evidence remain mandatory in that publisher.
 with redirect_stdout(sys.stderr):
  load(str(root/'tools'/module))[entry]()
 return True


if __name__=='__main__':
 if len(sys.argv)!=2:raise SystemExit('Expected macos-arm64, windows-x64 or linux-x64')
 print('publish='+str(publication_ready(sys.argv[1])).lower())
