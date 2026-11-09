#!/usr/bin/env bash
set -euo pipefail
source_dir=$(realpath "$1")
output_dir=$(realpath "$2")
version=$3
verifier_dir=$(dirname "$(realpath "$0")")
[[ "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]
cd "$source_dir/android-vision"
mkdir -p dist "$output_dir"
cleanup() {
  timeout 12s adb logcat -d > "$output_dir/release-logcat.txt" || true
  timeout 12s adb shell dumpsys activity activities > "$output_dir/release-activity.txt" || true
  for name in vision-home vision-menu vision-conversation vision-notice vision-update vision-ocean vision-ocean-card vision-ocean-thread vision-classic vision-language-english vision-language-arabic vision-welcome-replay vision-profile vision-message-photo; do
    timeout 12s adb pull "/sdcard/$name.png" "dist/$name.png" || true
  done
}
trap cleanup EXIT


assert_cold_launch() {
  local label=$1 ready=0 local_xml remote_xml preserve=${2:-0} launcher_repaired=0
  remote_xml="/sdcard/vision-${label}.xml"
  timeout 12s adb shell am force-stop com.osminog.vision
  if [[ "$preserve" != 1 ]]; then timeout 12s adb shell pm clear com.osminog.vision; fi
  timeout 20s adb shell am start -S -W -n com.osminog.vision/.MainActivity
  for attempt in $(seq 1 6); do
    local_xml="$output_dir/vision-${label}-${attempt}.xml"
    timeout 8s adb shell rm -f "$remote_xml" || true
    # Consume the complete XML through adb pull. grep -q on an adb pipe can
    # close the stream early and turn a match into failure under pipefail.
    if timeout 12s adb shell uiautomator dump "$remote_xml" > "$output_dir/vision-${label}-${attempt}.log" 2>&1 &&
       timeout 8s adb pull "$remote_xml" "$local_xml" >> "$output_dir/vision-${label}-${attempt}.log" 2>&1 &&
       python3 - "$local_xml" <<'PY'
import sys, xml.etree.ElementTree as ET
try:
    root=ET.parse(sys.argv[1]).getroot()
    ready=any(n.get('package')=='com.osminog.vision' for n in root.iter('node')) and not any("isn't responding" in n.get('text','') for n in root.iter('node'))
except (OSError, ET.ParseError):
    ready=False
sys.exit(0 if ready else 1)
PY
    then ready=1; cp "$local_xml" "$output_dir/vision-${label}.xml"; break; fi
    if [[ "$launcher_repaired" == 0 && -s "$local_xml" ]]; then
      timeout 12s adb logcat -d > "$output_dir/launcher-recovery-logcat.txt"
      if python3 "$verifier_dir/recognize-quickstep-anr.py" "$local_xml" "$output_dir/launcher-recovery-logcat.txt" > "$output_dir/launcher-recovery-target.txt"; then
        cp "$local_xml" "$output_dir/launcher-recovery-dialog.xml"
        timeout 12s adb shell screencap -p /sdcard/launcher-recovery.png
        timeout 12s adb pull /sdcard/launcher-recovery.png "$output_dir/launcher-recovery.png"
        read -r tap_x tap_y < "$output_dir/launcher-recovery-target.txt"
        timeout 8s adb shell input tap "$tap_x" "$tap_y"
        launcher_repaired=1
        printf '%s\\n' 'Recovered one verified com.android.launcher3 ANR; OSMINOG startup must still pass.' | tee "$output_dir/launcher-recovery.txt"
        sleep 1
        timeout 20s adb shell am start -S -W -n com.osminog.vision/.MainActivity
      fi
    fi
    sleep 1
  done
  timeout 12s adb shell screencap -p "/sdcard/vision-${label}.png"
  timeout 12s adb pull "/sdcard/vision-${label}.png" "$output_dir/vision-${label}.png"
  if [[ "$ready" != 1 ]]; then
    echo "Android $label cold start did not expose the OSMINOG application window; inspect preserved UI XML/logs" >&2
    return 1
  fi
  echo "ANDROID_${label^^}_COLD_START_PASS"
}

# Ensure the test window is reachable before injecting real touch events.
# Recover only the independently identified Quickstep ANR using the same strict
# XML + log recognizer as signed cold-launch checks; never suppress OSMINOG ANR.
timeout 30s adb install -r app/build/outputs/apk/debug/app-debug.apk
assert_cold_launch instrumentation-bootstrap

# Run the complete pinned test suite. The publisher owns the cold-start checks
# below; do not make publication depend on the source helper's streaming grep.
timeout --kill-after=20s 900s gradle :app:connectedDebugAndroidTest
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
v=tuple(map(int,sys.argv[1].split('.')))
minimum=72 if v >= (0,2,10) else 63 if v >= (0,2,9) else 53 if v >= (0,2,8) else 40 if v >= (0,2,7) else 29 if v >= (0,2,6) else 15 if v >= (0,2,4) else 7
assert tests>=minimum, f'Incomplete Android suite: {tests} < {minimum}'
print(f'ANDROID_INSTRUMENTATION_PASS {tests}')
PY

# Check both ordinary animated debug startup and the exact signed release APK.
timeout 30s adb install -r app/build/outputs/apk/debug/app-debug.apk
assert_cold_launch clean-launch
timeout 20s adb uninstall com.osminog.vision
if [[ "$version" == 0.2.5 ]]; then
  mkdir -p "$output_dir/previous"
  gh release download vision-android-v0.2.4 --repo jeep-jim/OSMINOG-Releases --pattern OSMINOG-Vision-0.2.4.apk --dir "$output_dir/previous"
  python3 - "$output_dir/previous/OSMINOG-Vision-0.2.4.apk" <<'PY'
import hashlib,pathlib,sys
p=pathlib.Path(sys.argv[1]);data=p.read_bytes()
assert len(data)==104972 and hashlib.sha256(data).hexdigest()=='620f0dd9fef96954c51a91475d510d125c91e10798875deafbe7aa606df2073d'
PY
  timeout 30s adb install "$output_dir/previous/OSMINOG-Vision-0.2.4.apk"
  assert_cold_launch previous
  timeout 12s adb shell dumpsys package com.osminog.vision > "$output_dir/package-before-upgrade.txt"
  timeout 30s adb install -r "$output_dir/OSMINOG-Vision-$version.apk"
  assert_cold_launch upgraded 1
  timeout 12s adb shell dumpsys package com.osminog.vision > "$output_dir/package-after-upgrade.txt"
  python3 - "$output_dir" <<'PY'
import pathlib,sys
p=pathlib.Path(sys.argv[1]);before=(p/'package-before-upgrade.txt').read_text();after=(p/'package-after-upgrade.txt').read_text()
def field(data,name):
    for line in data.splitlines():
        for token in line.strip().split():
            if token.startswith(name+"="): return token.split("=",1)[1].strip()
    raise AssertionError("Missing "+name)
assert field(before,'firstInstallTime')==field(after,'firstInstallTime'),'Application was reinstalled, not upgraded'
assert field(before,'versionName')=='0.2.4' and field(after,'versionName')=='0.2.5'
assert field(before,'versionCode')=='6' and field(after,'versionCode')=='7'
print('ANDROID_SIGNED_UPGRADE_024_TO_025_PASS; package data directory retained')
PY
  assert_cold_launch release 1
elif [[ "$version" == 0.2.4 ]]; then
  mkdir -p "$output_dir/previous"
  gh release download vision-android-v0.2.3 --repo jeep-jim/OSMINOG-Releases --pattern OSMINOG-Vision-0.2.3.apk --dir "$output_dir/previous"
  python3 - "$output_dir/previous/OSMINOG-Vision-0.2.3.apk" <<'PY'
import hashlib,pathlib,sys
assert hashlib.sha256(pathlib.Path(sys.argv[1]).read_bytes()).hexdigest()=='e2a8f3c8a03bae4e4bdfb51660a57af2d4e9be884e5768eeaeebd59a5f796fde'
PY
  timeout 30s adb install "$output_dir/previous/OSMINOG-Vision-0.2.3.apk"
  assert_cold_launch previous
  timeout 12s adb shell dumpsys package com.osminog.vision > "$output_dir/package-before-upgrade.txt"
  timeout 30s adb install -r "$output_dir/OSMINOG-Vision-$version.apk"
  assert_cold_launch upgraded 1
  timeout 12s adb shell dumpsys package com.osminog.vision > "$output_dir/package-after-upgrade.txt"
  python3 - "$output_dir" <<'PY'
import pathlib,sys
p=pathlib.Path(sys.argv[1]);before=(p/'package-before-upgrade.txt').read_text();after=(p/'package-after-upgrade.txt').read_text()
def field(data,name):
    for line in data.splitlines():
        if line.strip().startswith(name+"="): return line.split("=",1)[1].strip()
    raise AssertionError("Missing "+name)
assert field(before,'firstInstallTime')==field(after,'firstInstallTime'),'Install identity changed'
assert field(before,'versionName')=='0.2.3' and field(after,'versionName')=='0.2.4'
print('ANDROID_SIGNED_UPGRADE_023_TO_024_PASS')
PY
  assert_cold_launch release 1
else
  timeout 30s adb install "$output_dir/OSMINOG-Vision-$version.apk"
  assert_cold_launch release
fi
