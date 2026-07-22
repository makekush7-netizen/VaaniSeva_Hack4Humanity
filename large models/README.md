# Large Asset Files — Setup Guide

These files are **too large to be stored on GitHub** and need to be placed manually after cloning the project.

---

## Files in this folder

| File | Size | Purpose |
|------|------|---------|
| `hero.mp4` | ~12 MB | Background video on the Home page |
| `model_female.glb` | ~2.2 MB | 3D avatar model used in the VaaniSeva widget |

---

## Where to put them

After cloning the repo, copy these files to the exact paths below:

### 1. `hero.mp4`
Copy to:
```
VaaniSeva/website/public/hero.mp4
```

### 2. `model_female.glb`
Copy to:
```
VaaniSeva/website/public/models/model_female.glb
```

> **Note:** The `models/` folder inside `public/` may not exist yet. Create it if needed.

---

## Quick setup (copy-paste commands)

**Windows (PowerShell)** — run from the project root:
```powershell
# Make sure you're in the VaaniSeva project folder first
Copy-Item "large models\hero.mp4" "website\public\hero.mp4"
New-Item -ItemType Directory -Path "website\public\models" -Force
Copy-Item "large models\model_female.glb" "website\public\models\model_female.glb"
```

**Mac / Linux (Terminal)** — run from the project root:
```bash
cp "large models/hero.mp4" website/public/hero.mp4
mkdir -p website/public/models
cp "large models/model_female.glb" website/public/models/model_female.glb
```

---

## Why aren't these in Git?

GitHub rejects files larger than ~50 MB and strongly discourages files above 10 MB.
These assets are binary files that don't benefit from version control anyway.
They are listed in `.gitignore` so they will never be accidentally committed.
