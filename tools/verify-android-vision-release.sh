#!/usr/bin/env bash
set -euo pipefail
source_dir=$(realpath "$1")
output_dir=$(realpath "$2")
version=$3
[[ "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]
cd "$source_dir/android-vision"
bash tools/verify-emulator.sh
adb uninstall com.osminog.vision
adb install "$output_dir/OSMINOG-Vision-$version.apk"
adb shell rm -f /sdcard/vision-release.xml
adb shell am start -S -W -n com.osminog.vision/.MainActivity
ready=0
for attempt in $(seq 1 6); do
  timeout 12s adb shell uiautomator dump /sdcard/vision-release.xml >/dev/null 2>&1 || true
  if adb shell cat /sdcard/vision-release.xml 2>/dev/null | grep -q 'Меню OSMINOG'; then ready=1; break; fi
  sleep 1
done
adb shell screencap -p /sdcard/vision-release.png
adb pull /sdcard/vision-release.png "$output_dir/vision-release.png"
adb logcat -d > "$output_dir/release-logcat.txt"
test "$ready" -eq 1
