# Workshop robot banners

Fourteen 1200 x 300 illustrations for course openings and selected transitions.
Each filename stem has a PNG for embedding, a self-contained SVG, and an
editable Excalidraw scene. The smiling robot, navy ink, pale-blue canvas and
handwritten typography follow the evaluation-plan illustration in
`agentops\implementation-guidance\assets`.

| Stem | Topic props |
| --- | --- |
| `welcome` | Stepping stones and a star flag |
| `prework` | Sign-in key and prepared files |
| `instructor` | Easel, route, clock and checklist |
| `evaluate` | Magnified trace and mixed test outcomes |
| `ship` | Release package and checkpoint barrier |
| `observe-operate` | Telemetry heartbeat, alert and magnifier |
| `advanced` | Bug, wrench, repair loop and regression test |
| `host-setup` | Two numbered agent hosts and a cloud |
| `evidence` | Open evidence folder, records and a magnifier |
| `tooling` | Toolbox, wrench, screwdriver, ruler and command card |
| `criteria` | Clipboard, ruler, target and dart |
| `ready-to-run` | One Run button, cost coins and a result slip |
| `release-decision` | Green signal, incomplete checklist and unpressed stamp |

## Regenerate locally

From the repository root in PowerShell:

```powershell
& .\agentops\workshop\labs\01-evaluate\.venv\Scripts\python.exe .\agentops\workshop\assets\banners\generate_banners.py
```

The existing interpreter supplies Pillow and fontTools. The renderer reads
`C:\Windows\Fonts\comic.ttf` and `comicbd.ttf`; it installs nothing and makes no
network calls. PNGs are drawn at 4x resolution and downsampled. SVG lettering is
outlined from the same local fonts, with accessible text labels, so viewing the
SVG requires no font or image downloads. No font files are distributed.

Edit the messages and illustration primitives in `generate_banners.py` for
repeatable changes. All three formats use that same scene. Excalidraw preserves
individual paths, logical prop groups and editable black text; its native
hand-drawn font can look slightly different from the fixed PNG/SVG lettering.
Regeneration replaces manual edits to the exported scenes.

Add `--check` to verify existing exports without rewriting them. Checks include
exact copy, ink margins and spacing, 1200 x 300 PNGs, UTF-8 XML, local SVG
references, transparent diagram containers, unique Excalidraw IDs, generous
text dimensions, and agreement with the shared scene. Add `--contact-sheets`
for four disposable `.qa-contact-N.png` visual review sheets in this folder.
Inspect all banners and remove those sheets before committing assets.
