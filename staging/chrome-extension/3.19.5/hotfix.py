from __future__ import annotations

import base64
import hashlib
import json
import re
from pathlib import Path

ROOT = Path.cwd()
STAGE = Path(__file__).resolve().parent
OCTOPUS_SHA256 = "c212e02dfd2cc8fb29080da447dedb77cabe5ead63410e8968207cf63cb46260"


def install_asset(prefix: str, count: int, target: str, minimum: int, expected_sha: str | None = None) -> str:
    encoded = "".join((STAGE / "hero" / f"{prefix}-{i:02d}.b64").read_text(encoding="ascii").strip() for i in range(count))
    data = base64.b64decode(encoded, validate=True)
    if len(data) < minimum or data[:4] != b"RIFF" or data[8:12] != b"WEBP":
        raise SystemExit(f"invalid staged WebP: {prefix}, {len(data)} bytes")
    digest = hashlib.sha256(data).hexdigest()
    if expected_sha and digest != expected_sha:
        raise SystemExit(f"sha256 mismatch for {prefix}: {digest} != {expected_sha}")
    out = ROOT / target
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(data)
    return digest


human_sha = install_asset("human", 4, "assets/core/hero-human-3195.webp", 40000)
octopus_sha = install_asset("octopus-v3", 8, "assets/core/hero-octopus-ai-3195.webp", 44000, OCTOPUS_SHA256)
old_hero = ROOT / "assets/core/core-hero.webp"
if old_hero.exists():
    old_hero.unlink()

html_path = ROOT / "editor.html"
html = html_path.read_text(encoding="utf-8")
if "hero-human-3195.webp" not in html:
    pattern = re.compile(r'(<div id="emptyHint" class=")([^"]*\bcore-reset-launch\b[^"]*)(">)')
    match = pattern.search(html)
    if not match:
        raise SystemExit("emptyHint/core-reset-launch not found")
    classes = match.group(2)
    if "core-hero-launch" not in classes:
        classes += " core-hero-launch"
    replacement = (
        match.group(1) + classes + match.group(3) + "\n"
        '        <img class="core-hero-human" src="assets/core/hero-human-3195.webp" alt="" aria-hidden="true">\n'
        '        <img class="core-hero-octopus" src="assets/core/hero-octopus-ai-3195.webp" alt="" aria-hidden="true">'
    )
    html = html[:match.start()] + replacement + html[match.end():]
html_path.write_text(html, encoding="utf-8")

css_path = ROOT / "editor.css"
css = css_path.read_text(encoding="utf-8")
css = re.sub(r'\n?html\.osminog-native-file-drag #viewport:after\{[^\n]*\}\n?', "\n", css, count=1)
for marker in ("/* OSMINOG 3.19.4 · CORE HERO */", "/* OSMINOG 3.19.5 · SPLIT CORE HERO */"):
    if marker in css:
        css = css[:css.index(marker)].rstrip() + "\n\n"

css += r'''/* OSMINOG 3.19.5 · SPLIT CORE HERO */
.core-hero-launch{
  position:relative!important;
  overflow:visible!important;
  margin-top:150px!important;
  isolation:isolate
}
.core-hero-launch::before{
  content:"";
  position:absolute;
  z-index:0;
  left:50%;
  top:-245px;
  width:min(1000px,92vw);
  height:410px;
  transform:translateX(-50%);
  background:radial-gradient(ellipse at center,#665cff24 0,#0874ff0d 40%,transparent 72%);
  filter:blur(15px);
  pointer-events:none
}
.core-hero-human,.core-hero-octopus{
  position:absolute;
  pointer-events:none;
  user-select:none;
  -webkit-user-drag:none;
  object-fit:contain;
  filter:drop-shadow(0 22px 38px #0008);
  will-change:transform
}
.core-hero-human{
  z-index:4;
  width:clamp(180px,18vw,280px);
  height:auto;
  left:clamp(-230px,-17vw,-120px);
  top:clamp(-215px,-18vw,-140px);
  transform:rotate(-2deg);
  animation:coreHeroHumanFloat 6.4s ease-in-out infinite
}
.core-hero-octopus{
  z-index:1;
  width:clamp(560px,60vw,820px);
  height:auto;
  left:50%;
  top:-335px;
  transform:translateX(-31%);
  animation:coreHeroOctopusFloat 7.2s ease-in-out infinite
}
.core-hero-launch > :not(.core-hero-human):not(.core-hero-octopus){position:relative;z-index:3}
@keyframes coreHeroHumanFloat{0%,100%{transform:translateY(0) rotate(-2deg)}50%{transform:translateY(-6px) rotate(-1deg)}}
@keyframes coreHeroOctopusFloat{0%,100%{transform:translate(-31%,0)}50%{transform:translate(-31%,-5px)}}
@media(max-width:980px){
 .core-hero-launch{margin-top:130px!important}
 .core-hero-human{width:210px;left:-135px;top:-175px}
 .core-hero-octopus{width:690px;top:-290px;transform:translateX(-30%)}
 @keyframes coreHeroOctopusFloat{0%,100%{transform:translate(-30%,0)}50%{transform:translate(-30%,-4px)}}
}
@media(max-width:760px){
 .core-hero-launch{margin-top:105px!important}
 .core-hero-human{width:150px;left:-70px;top:-125px}
 .core-hero-octopus{width:500px;top:-220px;transform:translateX(-34%)}
 @keyframes coreHeroOctopusFloat{0%,100%{transform:translate(-34%,0)}50%{transform:translate(-34%,-4px)}}
}
@media(max-height:760px) and (min-width:761px){
 .core-hero-launch{margin-top:110px!important}
 .core-hero-human{top:-165px}
 .core-hero-octopus{top:-270px;width:700px}
}
@media(prefers-reduced-motion:reduce){.core-hero-human,.core-hero-octopus{animation:none}}
'''
css_path.write_text(css.rstrip() + "\n", encoding="utf-8")

editor_path = ROOT / "editor.js"
editor = editor_path.read_text(encoding="utf-8")
legacy_marker = "/* OSMINOG 3.19.3 · native desktop file drop recovery */"
if legacy_marker in editor:
    editor = editor[:editor.index(legacy_marker)].rstrip() + "\n"
editor = editor.replace('chrome.storage.local.set({briefCraftLastCachedImage:src,briefCraftLastCachedImageAt:Date.now()}).catch(()=>{});', '', 1)
if "let nativeDropBusy=false" not in editor:
    anchor = 'const viewport=$("#viewport");viewport.addEventListener("pointerdown"'
    if anchor not in editor:
        raise SystemExit("viewport pointerdown anchor not found")
    drop = '''const viewport=$("#viewport");let nativeDropBusy=false;viewport.addEventListener("dragover",e=>{if(!Array.from(e.dataTransfer?.types||[]).includes("Files"))return;e.preventDefault();e.dataTransfer.dropEffect="copy"});viewport.addEventListener("drop",async e=>{if(!Array.from(e.dataTransfer?.types||[]).includes("Files"))return;e.preventDefault();e.stopPropagation();if(nativeDropBusy)return;const files=[...(e.dataTransfer?.files||[])];if(!files.length)return;nativeDropBusy=true;try{await importFiles(files,worldPoint(e.clientX,e.clientY),"auto");showToast(state.language==="ru"?`Добавлено: ${files.length}`:`Added: ${files.length}`)}catch(error){console.error("OSMINOG file drop",error);showToast(error?.message||String(error))}finally{nativeDropBusy=false}});viewport.addEventListener("pointerdown"'''
    editor = editor.replace(anchor, drop, 1)
editor_path.write_text(editor, encoding="utf-8")

manifest_path = ROOT / "manifest.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
fixed_key = manifest.get("key")
if not fixed_key:
    raise SystemExit("fixed Chrome extension key missing")
manifest["version"] = "3.19.5"
manifest["version_name"] = "3.19.5"
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

build = {
    "product": "OSMINOG",
    "platform": "chrome-extension",
    "version": "3.19.5",
    "codename": "SPLIT CORE HERO",
    "baseVersion": "3.19.3-public / 3.19.4-source",
    "artifact": "OSMINOG-Chrome-3.19.5-SPLIT-CORE-HERO-NATIVE-DROP.zip",
    "manifestAtRoot": True,
    "manifestVersion": "3.19.5",
    "fixedManifestKeyPreserved": True,
    "runtimeVerified": False,
    "ownerRuntime": "Poseidon remains owner-only for OSMINOG source changes",
    "binaryInGitHub": True,
    "notes": "Split approved transparent human and OSMINOG/AI hero layers; remove duplicate capture drop runtime; keep one guarded viewport-native file drop path.",
    "status": "manual-test",
    "versionName": "3.19.5",
    "build": "3.19.5",
    "channel": "dev",
    "release": "SPLIT-CORE-HERO",
}
(ROOT / "OSMINOG_BUILD.json").write_text(json.dumps(build, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

readme = ROOT / "versions/3.19.5/README.md"
readme.parent.mkdir(parents=True, exist_ok=True)
readme.write_text("""# OSMINOG 3.19.5 — Split Core Hero

- Approved human is a separate transparent layer on the left of the empty-state card.
- Approved red octopus + AI logos are a separate transparent layer above/right of the card.
- No banana/stars or combined 3.19.4 hero layer.
- Hero layers use pointer-events:none and responsive placement.
- Native file drop uses one guarded viewport path; the duplicate 3.19.3 capture-level handler and fullscreen overlay are removed.
- Runtime UI verification remains manual after update.
""", encoding="utf-8")

print("human_sha256", human_sha)
print("octopus_sha256", octopus_sha)
print("fixed_identity_sha256", hashlib.sha256(fixed_key.encode()).hexdigest())
