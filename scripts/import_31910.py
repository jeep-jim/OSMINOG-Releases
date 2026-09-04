from pathlib import Path
import json
import sys

root = Path(sys.argv[1])

# Move the welcome heading/content block visibly higher without touching the hero art.
p = root / "editor.css"
s = p.read_text(encoding="utf-8")
old_title = '.core-hero-launch h2.core-hero-title{max-width:590px!important;margin:28px auto 12px!important;font-size:clamp(30px,3.25vw,44px)!important;line-height:1.04!important;color:var(--text)!important;font-weight:800!important;letter-spacing:-.035em!important}'
new_title = '.core-hero-launch h2.core-hero-title{max-width:590px!important;margin:-10px auto 12px!important;font-size:clamp(30px,3.25vw,44px)!important;line-height:1.04!important;color:var(--text)!important;font-weight:800!important;letter-spacing:-.035em!important}'
assert old_title in s, "3.19.9 hero title target missing"
s = s.replace(old_title, new_title, 1)
if '/* OSMINOG 3.19.10 · HERO TITLE LIFT */' not in s:
    s = s.rstrip() + '\n\n/* OSMINOG 3.19.10 · HERO TITLE LIFT */\n' + \
        '.core-hero-launch h2.core-hero-title{margin-top:-10px!important}\n'
p.write_text(s, encoding="utf-8")

# Bump package identity only; all 3.19.9 functional fixes remain intact.
p = root / "manifest.json"
m = json.loads(p.read_text(encoding="utf-8"))
m["version"] = "3.19.10"
m["version_name"] = "3.19.10"
p.write_text(json.dumps(m, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

p = root / "OSMINOG_BUILD.json"
b = json.loads(p.read_text(encoding="utf-8"))
b.update({
    "version":"3.19.10","versionName":"3.19.10","build":"3.19.10",
    "codename":"HERO TITLE LIFT","baseVersion":"3.19.9",
    "artifact":"OSMINOG-Chrome-3.19.10-HERO-TITLE-LIFT.zip",
    "manifestVersion":"3.19.10","release":"HERO-TITLE-LIFT",
    "notes":"Welcome heading/content flow raised by 38 px versus 3.19.9; original hero art and all provider/canvas fixes preserved."
})
p.write_text(json.dumps(b, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
