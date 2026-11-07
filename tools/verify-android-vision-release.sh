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

# Run the complete pinned test suite. The publisher owns the cold-start checks
# below; do not make publication depend on the source helper's streaming grep.
timeout --kill-after=20s 360s gradle :app:connectedDebugAndroidTest
python3 - <<'PY'
import pathlib, xml.etree.ElementTree as ET
reports=list(pathlib.Path('app/build/outputs/androidTest-results/connected/debug').glob('TEST-*.xml'))
assert reports, 'No Android instrumentation results'
tests=0
for report in reports:
    root=ET.parse(report).getroot()
    assert int(root.get('failures','0'))==0 and int(root.get('errors','0'))==0, str(report)
    assert int(root.get('skipped','0'))==0, 'Skipped Android tests'
    tests+=int(root.get('tests','0'))
assert tests>=7, f'Incomplete Android suite: {tests}'
print(f'ANDROID_INSTRUMENTATION_PASS {tests}')
PY

assert_cold_launch() {
  local label=$1 ready=0 local_xml remote_xml
  remote_xml="/sdcard/vision-${label}.xml"
  timeout 12s adb shell am force-stop com.osminog.vision
  timeout 12s adb shell pm clear com.osminog.vision
  timeout 20s adb shell am start -S -W -n com.osminog.vision/.MainActivity
  for attempt in $(seq 1 12); do
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

# Check both ordinary animated debug startup and the exact signed release APK.
timeout 30s adb install -r app/build/outputs/apk/debug/app-debug.apk
assert_cold_launch clean-launch
timeout 20s adb uninstall com.osminog.vision
timeout 30s adb install "$output_dir/OSMINOG-Vision-$version.apk"
assert_cold_launch release
