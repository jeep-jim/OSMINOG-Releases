#!/usr/bin/env bash
set -euo pipefail
output_dir=$(realpath "$1")
version=$2
case "$version" in
  0.2.10) previous=0.2.9; previous_code=11; next_code=12; previous_size=470580; previous_hash=14aaa7a20a125e2493090774ea792f577e8e25d810bda9e674bdbe2537c4b9bc; label=029_TO_0210 ;;
  0.2.11) previous=0.2.10; previous_code=12; next_code=13; previous_size=511600; previous_hash=547d078ad1c34526d7f7ea821ddc6aec9f281c2785cf29a511950bcdd2eea4c7; label=0210_TO_0211 ;;
  0.2.12) previous=0.2.11; previous_code=13; next_code=14; previous_size=515783; previous_hash=15caddbff706b783b3874285a64cc00a22e1b192b6b103b6ede67bd78e707ce8; label=0211_TO_0212 ;;
  *) exit 0 ;;
esac
verifier_dir=$(dirname "$(realpath "$0")")
mkdir -p "$output_dir/previous-intents"
gh release download "vision-android-v$previous" --repo jeep-jim/OSMINOG-Releases --pattern "OSMINOG-Vision-$previous.apk" --dir "$output_dir/previous-intents"
python3 - "$output_dir/previous-intents/OSMINOG-Vision-$previous.apk" "$previous_size" "$previous_hash" <<'PYVERIFY'
import hashlib,pathlib,sys
raw=pathlib.Path(sys.argv[1]).read_bytes()
assert len(raw)==int(sys.argv[2])
assert hashlib.sha256(raw).hexdigest()==sys.argv[3]
PYVERIFY
# This is a disposable CI emulator, not the user's device. Establish the previous
# signed installation ONCE; never uninstall or clear data between it and upgrade.
timeout 20s adb uninstall com.osminog.vision
timeout 30s adb install "$output_dir/previous-intents/OSMINOG-Vision-$previous.apk"
timeout 20s adb shell am start -S -W -n com.osminog.vision/.MainActivity
sleep 2
timeout 12s adb shell dumpsys package com.osminog.vision > "$output_dir/intent-upgrade-before.txt"
timeout 30s adb install -r "$output_dir/OSMINOG-Vision-$version.apk"
timeout 20s adb shell am start -S -W -n com.osminog.vision/.MainActivity
sleep 2
timeout 12s adb shell dumpsys package com.osminog.vision > "$output_dir/intent-upgrade-after.txt"
python3 - "$output_dir" "$previous" "$version" "$previous_code" "$next_code" "$label" <<'PY'
import json,pathlib,re,sys
p=pathlib.Path(sys.argv[1]);before=(p/'intent-upgrade-before.txt').read_text();after=(p/'intent-upgrade-after.txt').read_text()
def field(text,name):
    m=re.search(r'(?m)^\s*'+re.escape(name)+r'=(.+)$',text)
    assert m,'Missing '+name
    return m.group(1).strip()
def token(text,name):
    m=re.search(r'\b'+re.escape(name)+r'=([^\s]+)',text)
    assert m,'Missing '+name
    return m.group(1)
# Compare the COMPLETE date AND time, not just the first whitespace-delimited token.
assert field(before,'firstInstallTime')==field(after,'firstInstallTime'),'Installation identity changed'
def app_identity(text):
    # Android 15 dumpsys uses appId; older builds use userId for this field.
    values=re.findall(r'(?m)^\s*(?:appId|userId)=(\d+)\s*$',text)
    assert values and len(set(values))==1,'Missing or ambiguous application identity'
    return values[0]
assert app_identity(before)==app_identity(after),'Application identity changed'
assert token(before,'versionCode')==sys.argv[4] and token(after,'versionCode')==sys.argv[5]
assert token(before,'versionName')==sys.argv[2] and token(after,'versionName')==sys.argv[3]
(p/'intent-upgrade-verification.json').write_text(json.dumps({'from':sys.argv[2],'to':sys.argv[3],'sameFirstInstallTime':True,'sameUid':True,'inPlaceInstall':True,'historyContentIndependentlyChecked':False},indent=2)+'\n')
print('SIGNED_'+sys.argv[6]+'_IN_PLACE_INSTALL_PASS; history content covered separately by local migration tests')
PY
ready=0
repaired=0
for attempt in 1 2 3 4 5 6; do
  xml="$output_dir/intent-upgraded-$attempt.xml"
  timeout 4s adb shell rm -f /sdcard/intent-upgraded.xml || true
  if timeout 10s adb shell uiautomator dump /sdcard/intent-upgraded.xml > "$output_dir/intent-upgraded-$attempt.log" 2>&1 && timeout 4s adb pull /sdcard/intent-upgraded.xml "$xml" >> "$output_dir/intent-upgraded-$attempt.log" 2>&1; then
    if python3 - "$xml" <<'PY'
import sys,xml.etree.ElementTree as ET
root=ET.parse(sys.argv[1]).getroot();nodes=list(root.iter('node'))
text=' '.join(n.get('text','') for n in nodes)
ready=any(n.get('package')=='com.osminog.vision' for n in nodes) and "isn't responding" not in text
sys.exit(0 if ready else 1)
PY
    then ready=1; cp "$xml" "$output_dir/intent-upgraded.xml"; break; fi
    if [[ "$repaired" == 0 ]]; then
      timeout 12s adb logcat -d > "$output_dir/intent-upgrade-logcat.txt"
      if python3 "$verifier_dir/recognize-quickstep-anr.py" "$xml" "$output_dir/intent-upgrade-logcat.txt" > "$output_dir/intent-upgrade-quickstep.txt"; then
        read -r x y < "$output_dir/intent-upgrade-quickstep.txt"
        timeout 6s adb shell input tap "$x" "$y"
        repaired=1
      fi
    fi
  fi
  sleep 1
done
timeout 12s adb shell screencap -p /sdcard/intent-upgraded.png
timeout 12s adb pull /sdcard/intent-upgraded.png "$output_dir/intent-upgraded.png"
[[ "$ready" == 1 ]] || { echo 'Upgraded OSMINOG window not visible' >&2; exit 1; }
echo "SIGNED_${label}_COLD_LAUNCH_PASS"
