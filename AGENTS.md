# AGENTS.md

## Cursor Cloud specific instructions

### Overview
This is the **Odoo 19.1 alpha** source code — a Python-based ERP/CRM platform. The main entry point is `./odoo-bin`.

### Services
| Service | Port | Notes |
|---------|------|-------|
| **Odoo HTTP** | 8069 | `python3 odoo-bin --config=odoo-dev.conf --dev=reload` |
| **PostgreSQL 16** | 5432 | Must be started before Odoo: `sudo pg_ctlcluster 16 main start` |

### Running the dev server
```bash
sudo pg_ctlcluster 16 main start
python3 odoo-bin --config=odoo-dev.conf --dev=reload
```
Default admin credentials: `admin` / `admin` (database `odoo_dev`).

### Linting
```bash
ruff check --config ruff.toml <files_or_dirs>
```
`ruff` is installed in `~/.local/bin` (already on PATH via `~/.bashrc`).

### Running tests
```bash
python3 odoo-bin --config=odoo-dev.conf --test-tags=/<module>:<TestClass> --stop-after-init --no-http
```
Example: `--test-tags=/base:TestSafeEval`.

### Key gotchas
- PostgreSQL must be started manually (`sudo pg_ctlcluster 16 main start`) since systemd services don't auto-start in this environment.
- Python packages are installed system-wide with `--break-system-packages` (no venv) since this is a disposable cloud VM.
- The config file `odoo-dev.conf` lives in the repo root and sets `addons_path`, `db_name=odoo_dev`, etc.
- `wkhtmltopdf` is not installed; PDF report rendering will not work but is not needed for most development tasks.
- The `--dev=reload` flag enables auto-reload on Python file changes.
