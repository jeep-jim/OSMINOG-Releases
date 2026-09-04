from pathlib import Path
import json
import sys

root = Path(sys.argv[1])

# 1) Start with the right inspector collapsed on first entry.
p = root / "editor.html"
s = p.read_text(encoding="utf-8")
old = '<aside id="inspector" class="inspector glass">'
new = '<aside id="inspector" class="inspector glass collapsed">'
if old not in s and new not in s:
    raise SystemExit("inspector markup target missing")
if old in s:
    s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8")

# 2) Keep the primary welcome button readable on Light hover/focus.
p = root / "osminog-product-core-recovery.css"
s = p.read_text(encoding="utf-8")
marker = "OSMINOG 3.19.11 · LIGHT PRIMARY HOVER + CLOSED INSPECTOR"
patch = r'''

/* OSMINOG 3.19.11 · LIGHT PRIMARY HOVER + CLOSED INSPECTOR */
html[data-theme="light"] .primary-btn:hover,
html[data-theme="light"] .primary-btn:focus-visible,
html[data-theme="light"] .core-hero-launch .empty-launch-actions>.primary-btn:hover,
html[data-theme="light"] .core-hero-launch .empty-launch-actions>.primary-btn:focus-visible{
  color:#fff!important;
  background:linear-gradient(120deg,#536dff,#7b4dff)!important;
  border-color:#6c5cff!important;
  opacity:1!important;
  -webkit-text-fill-color:#fff!important
}
html[data-theme="light"] .core-hero-launch .empty-launch-actions>.primary-btn:hover svg,
html[data-theme="light"] .core-hero-launch .empty-launch-actions>.primary-btn:focus-visible svg{
  color:#fff!important;
  stroke:currentColor!important;
  opacity:1!important
}
'''
if marker not in s:
    s = s.rstrip() + patch + "\n"
p.write_text(s, encoding="utf-8")

# 3) Version metadata.
p = root / "manifest.json"
m = json.loads(p.read_text(encoding="utf-8"))
m["version"] = "3.19.11"
m["version_name"] = "3.19.11"
p.write_text(json.dumps(m, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

p = root / "OSMINOG_BUILD.json"
b = json.loads(p.read_text(encoding="utf-8"))
b.update({
    "version":"3.19.11",
    "versionName":"3.19.11",
    "build":"3.19.11",
    "codename":"LIGHT HOVER + CLOSED INSPECTOR",
    "baseVersion":"3.19.10",
    "artifact":"OSMINOG-Chrome-3.19.11-LIGHT-HOVER-CLOSED-INSPECTOR.zip",
    "manifestVersion":"3.19.11",
    "release":"LIGHT-HOVER-CLOSED-INSPECTOR",
    "notes":"Light-theme primary hover remains readable; the right inspector starts collapsed on first workspace entry. All 3.19.10 hero, localization, provider and canvas fixes are preserved."
})
p.write_text(json.dumps(b, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
