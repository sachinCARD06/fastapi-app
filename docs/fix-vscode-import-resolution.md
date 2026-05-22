# Fix: Unresolved FastAPI Imports in VSCode

**Symptom:** `Import "fastapi.middleware.cors" could not be resolved` (or similar errors for any installed package) shown as red underlines in VSCode, even though the package is installed and the app runs fine.

**Root cause:** VSCode/Pylance is using the system Python instead of the project's virtual environment, so it cannot find packages installed inside `venv/`.

---

## Step 1 — Confirm the venv exists and has the packages

```bash
source venv/bin/activate
pip show fastapi
```

Expected output includes `Location: .../venv/lib/pythonX.XX/site-packages`. If the package is missing, install dependencies first:

```bash
pip install -r requirements-dev.txt
```

---

## Step 2 — Create (or update) `.vscode/settings.json`

Create the file at the project root if it does not exist:

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
  "python.analysis.extraPaths": ["${workspaceFolder}"]
}
```

`${workspaceFolder}` resolves to the directory you opened in VSCode — no hardcoded paths needed.

---

## Step 3 — Select the interpreter in VSCode

1. Open the Command Palette: **Cmd+Shift+P** (Mac) / **Ctrl+Shift+P** (Windows/Linux)
2. Type and select: **Python: Select Interpreter**
3. Choose the entry that shows `./venv/bin/python` or `venv` in its path

If the venv entry is not listed, click **Enter interpreter path…** and paste:

```
./venv/bin/python
```

---

## Step 4 — Reload the Pylance language server

After switching the interpreter, force a fresh analysis:

1. Open the Command Palette
2. Run: **Python: Restart Language Server**

The red underlines should disappear within a few seconds as Pylance re-indexes the venv packages.

---

## Verification

Open any file that has the previously failing import (e.g. `app/main.py`) and confirm there are no import errors. You can also hover over `CORSMiddleware` — Pylance should show its type signature.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `venv` entry not in interpreter list | Use **Enter interpreter path…** and point to `./venv/bin/python` manually |
| Errors return after reopening VSCode | Ensure `.vscode/settings.json` is saved and committed |
| New packages still unresolved after `pip install` | Run **Python: Restart Language Server** again |
| Multiple Python versions on the machine | Verify `python.defaultInterpreterPath` points to the venv, not `/usr/bin/python3` |
