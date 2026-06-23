# New machine setup

Everything lives in this repo. After cloning, do these steps in order.

---

## 1 — Clone & Python env

```bash
git clone https://github.com/eeberman/sports-predict-ee.git
cd sports-predict-ee
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

---

## 2 — Secrets (.env)

Copy the template and fill in real values. **Never commit the filled-in file.**

```bash
cp .env.example .env
# edit .env with your real keys:
#   SPORTSPREDICT_API_KEY, ODDS_API_KEY, FOOTBALL_DATA_API_KEY,
#   R2_ACCOUNT_ID, R2_ACCESS_KEY_ID (or AWS_ACCESS_KEY_ID), R2_SECRET_ACCESS_KEY
```

R2 credentials: Cloudflare dashboard → R2 → Manage API tokens.

---

## 3 — Claude Code / Claude Agent SDK

Install Claude Code:
```bash
npm install -g @anthropic/claude-code
```

Or download the desktop app from claude.ai.

### Install the predict-game skill

The skill file and its references live at `claude/skills/predict-game/` in this repo.
Copy them to the Claude skills directory:

**Mac / Linux:**
```bash
mkdir -p ~/.claude/skills/predict-game/references
cp claude/skills/predict-game/skill.md ~/.claude/skills/predict-game/skill.md
cp claude/skills/predict-game/references/*.md ~/.claude/skills/predict-game/references/
```

**Windows (PowerShell):**
```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.claude\skills\predict-game\references"
Copy-Item claude\skills\predict-game\skill.md "$env:USERPROFILE\.claude\skills\predict-game\skill.md"
Copy-Item claude\skills\predict-game\references\*.md "$env:USERPROFILE\.claude\skills\predict-game\references\"
```

### Restore memory

Memory files give Claude context about decisions made in prior sessions.
Find your project memory path — it's based on the absolute path of this repo.

**Mac / Linux:**
```bash
PROJ=$(pwd | sed 's|/|-|g' | sed 's|^-||')
mkdir -p ~/.claude/projects/$PROJ/memory
cp claude/memory/*.md ~/.claude/projects/$PROJ/memory/
```

**Windows (PowerShell):**
```powershell
$proj = (Get-Location).Path -replace '[:\\]','-' -replace '^-',''
New-Item -ItemType Directory -Force "$env:USERPROFILE\.claude\projects\$proj\memory"
Copy-Item claude\memory\*.md "$env:USERPROFILE\.claude\projects\$proj\memory\"
```

---

## 4 — Verify

```bash
# smoke-test the forecasting module
python -m forecasting.devig_bakeoff --summary

# check results log
python -c "import csv; rows=list(csv.DictReader(open('outputs/results/results_log.csv'))); print(f'{len(rows)} rows in log')"
```

Then open Claude Code in the `sports-predict-ee/` directory and run `/predict-game` for the next match.
