# Clear all Astro / dev caches

Paths are relative to the project root (`astro/`).

## What gets cleared

| Location | Contents |
|----------|----------|
| `data/cache/` | SQLite metadata, decision logs, eval reports, etc. (see below) |
| `.pytest_cache/` | Pytest cache |
| `**/__pycache__/` | Python bytecode caches under the repo (excluding `.venv`) |

**Not** removed: `data/features/` (parquet), model checkpoints under `models/checkpoints/`, or `.venv/`.

---

## PowerShell (Windows)

From the project root:

```powershell
# Astro app cache (create parent if missing)
if (Test-Path "data\cache") { Remove-Item -Recurse -Force "data\cache" }

# Pytest
if (Test-Path ".pytest_cache") { Remove-Item -Recurse -Force ".pytest_cache" }

# Python __pycache__ (skip .venv)
Get-ChildItem -Path . -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue |
  Where-Object { $_.FullName -notmatch '\\\.venv\\' } |
  Remove-Item -Recurse -Force
```

---

## Bash (macOS / Linux)

```bash
cd "$(dirname "$0")/.." 2>/dev/null || true
rm -rf data/cache .pytest_cache
find . -path ./.venv -prune -o -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
```

---

## Optional: only decision / eval artifacts

Keep SQLite but drop logs:

```powershell
Remove-Item -Force -ErrorAction SilentlyContinue data\cache\decision_logs\*
Remove-Item -Force -ErrorAction SilentlyContinue data\cache\eval_reports\*
```

---

## After clearing

- Next API run recreates `data/cache/astro_meta.sqlite` and new decision rows as needed.
- Re-run `bootstrap_fused_features` or your pipelines if you also deleted feature parquet (not covered here).

From **CMD** with your project folder as `C:\Users\Shubhankar\Desktop\astro`, you can clear caches like this:

### Remove Astro `data\cache` (SQLite, decision logs, eval reports, …)
```cmd
rmdir /s /q data\cache
```

### Remove pytest cache
```cmd
rmdir /s /q .pytest_cache
```

### Remove all `__pycache__` folders under the project (CMD one-liner with `for`)
```cmd
for /d /r %d in (__pycache__) do @if exist "%d" rmdir /s /q "%d"
```

**Note:** That `for` loop walks **every** subdirectory, including `.venv`. To **skip** `.venv`, run this instead:

```cmd
for /f "delims=" %i in ('dir /s /b /ad __pycache__ ^| findstr /v "\\.venv\\"') do @rmdir /s /q "%i"
```

### All together (safe for `.venv` on `__pycache__`)
```cmd
cd /d C:\Users\Shubhankar\Desktop\astro
if exist data\cache rmdir /s /q data\cache
if exist .pytest_cache rmdir /s /q .pytest_cache
for /f "delims=" %i in ('dir /s /b /ad __pycache__ ^| findstr /v "\\.venv\\"') do @rmdir /s /q "%i"
```

If `data\cache` doesn’t exist yet, the `if exist` line simply does nothing. After this, the app will recreate `data\cache` when you run decisions or the API again.