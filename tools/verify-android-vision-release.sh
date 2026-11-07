#!/usr/bin/env bash
set -euo pipefail
source_dir=$(realpath "$1")
output_dir=$(realpath "$2")
version=$3
[[ "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]
cd "$source_dir/android-vision"
mkdir -p dist "$output_dir"
cleanup() {
  timeout 12s adb logcat -d > "$output_dir/release-logcat.txt" || true
  timeout 12s adb shell dumpsys activity activities > "$output_dir/release-activity.txt" || true
  for name in vision-home vision-menu vision-conversation vision-notice vision-update; do
    timeout 12s adb pull "/sdcard/$name.png" "dist/$name.png" || true
  done
}
trap cleanup EXIT

# All instrumentation assertions remain mandatory. The publisher owns the
# ordinary cold-start checks below and reads complete UI XML, not streaming grep.
timeout --kill-after=20s 360s gradle :app:connectedDebugAndroidTest
python3 - "$version" <<'PY'
import pathlib, sys, xml.etree.ElementTree as ET
reports=list(pathlib.Path('app/build/outputs/androidTest-results/connected/debug').glob('TEST-*.xml'))
assert reports, 'No Android instrumentation results'
tests=0
for report in reports:
    root=ET.parse(report).getroot()
    assert int(root.get('failures','0'))==0 and int(root.get('errors','0'))==0, str(report)
    assert int(root.get('skipped','0'))==0, 'Skipped Android tests'
    tests+=int(root.get('tests','0'))
minimum=14 if tuple(map(int,sys.argv[1].split('.'))) >= (0,2,4) else 7
assert tests>=minimum, f'Incomplete Android suite: {tests} < {minimum}'
print(f'ANDROID_INSTRUMENTATION_PASS {tests}')
PY

assert_cold_launch() {
  local label=$1 ready=0 local_xml remote_xml preserve=${2:-0}
  remote_xml="/sdcard/vision-${label}.xml"
  timeout 12s adb shell am force-stop com.osminog.vision
  if [[ "$preserve" != 1 ]]; then timeout 12s adb shell pm clear com.osminog.vision; fi
  timeout 20s adb shell am start -S -W -n com.osminog.vision/.MainActivity
  for attempt in $(seq 1 12); do
    local_xml="$output_dir/vision-${label}-${attempt}.xml"
    timeout 8s adb shell rm -f "$remote_xml" || true
    if timeout 12s adb shell uiautomator dump "$remote_xml" > "$output_dir/vision-${label}-${attempt}.log" 2>&1 &&
       timeout 8s adb pull "$remote_xml" "$local_xml" >> "$output_dir/vision-${label}-${attempt}.log" 2>&1 &&
       python3 - "$local_xml" <<'PY'
import sys, xml.etree.ElementTree as ET
try:
    root=ET.parse(sys.argv[1]).getroot()
    ready=any(n.get('package')=='com.osminog.vision' and
              'Меню OSMINOG' in (n.get('content-desc','')+' '+n.get('text',''))
              for n in root.iter('node'))
except (OSError, ET.ParseError):
    ready=False
sys.exit(0 if ready else 1)
PY
    then ready=1; cp "$local_xml" "$output_dir/vision-${label}.xml"; break; fi
    sleep 1
  done
  timeout 12s adb shell screencap -p "/sdcard/vision-${label}.png"
  timeout 12s adb pull "/sdcard/vision-${label}.png" "$output_dir/vision-${label}.png"
  if [[ "$ready" != 1 ]]; then
    echo "Android $label cold start did not expose the OSMINOG menu; inspect preserved UI XML/logs" >&2
    return 1
  fi
  echo "ANDROID_${label^^}_COLD_START_PASS"
}

timeout 30s adb install -r app/build/outputs/apk/debug/app-debug.apk
assert_cold_launch clean-launch
timeout 20s adb uninstall com.osminog.vision
if [[ "$version" == 0.2.4 ]]; then
  mkdir -p "$output_dir/previous"
  gh release download vision-android-v0.2.3 --repo jeep-jim/OSMINOG-Releases --pattern OSMINOG-Vision-0.2.3.apk --dir "$output_dir/previous"
  python3 - "$output_dir/previous/OSMINOG-Vision-0.2.3.apk" <<'PY'
import hashlib,pathlib,sys
assert hashlib.sha256(pathlib.Path(sys.argv[1]).read_bytes()).hexdigest()=='e2a8f3c8a03bae4e4bdfb51660a57af2d4e9be884e5768eeaeebd59a5f796fde'
PY
  timeout 30s adb install "$output_dir/previous/OSMINOG-Vision-0.2.3.apk"
  assert_cold_launch previous
  timeout 12s adb shell dumpsys package com.osminog.vision > "$output_dir/package-before-upgrade.txt"
  # No uninstall, no pm clear between the previous release and this startup.
  timeout 30s adb install -r "$output_dir/OSMINOG-Vision-$version.apk"
  assert_cold_launch upgraded 1
  timeout 12s adb shell dumpsys package com.osminog.vision > "$output_dir/package-after-upgrade.txt"
  python3 - "$output_dir" <<'PY'
import pathlib,re,sys
p=pathlib.Path(sys.argv[1])
before=(p/'package-before-upgrade.txt').read_text();after=(p/'package-after-upgrade.txt').read_text()
def installed(text):
    match=re.search(r'firstInstallTime=(.+)',text)
    assert match, 'Missing firstInstallTime'
    return match.group(1).strip()
assert installed(before)==installed(after), 'Install identity changed'
assert 'versionName=0.2.3' in before and 'versionName=0.2.4' in after
print('ANDROID_SIGNED_UPGRADE_023_TO_024_PASS; no account/history fixture is implied')
PY
else
  timeout 30s adb install "$output_dir/OSMINOG-Vision-$version.apk"
fi
assert_cold_launch release
