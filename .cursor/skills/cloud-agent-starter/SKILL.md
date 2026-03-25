---
name: cloud-agent-starter
description: Practical first-run playbook for Cloud agents to bootstrap, run, and test this Odoo codebase quickly.
---

# Cloud Agent Starter (Odoo Core)

## Scope
Use this skill first when you are new to this repository and need immediate, practical run and test commands.

Repository layout overview:
- `odoo/`: core framework services, ORM, CLI, server internals.
- `addons/`: official modules (business logic, views, web assets, tours, tests).
- `setup/` and packaging files: distro/build packaging helpers, not day-to-day app coding.

## 0) First-time environment bootstrap

Run these commands from repo root (`/workspace`):

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip wheel
pip install -r requirements.txt
```

PostgreSQL quick setup (local Cloud VM):

```bash
# only if role/db do not exist yet
createuser -s "$USER" || true
createdb "odoo_cloud" || true
```

If PostgreSQL is remote or secured, use explicit DB parameters in all `odoo-bin` commands:
- `--db_host=<host>`
- `--db_port=<port>`
- `--db_user=<user>`
- `--db_password=<password>`

## 1) Login and app startup (fastest working path)

### Start server in dev mode

```bash
source .venv/bin/activate
python3 odoo-bin -d odoo_cloud --addons-path=addons,odoo/addons --dev=xml,reload
```

Then open:
- `http://127.0.0.1:8069`

First-run UI login defaults:
- Database manager: create/select `odoo_cloud`.
- Main credentials after base install:
  - login: `admin`
  - password: `admin`

If DB manager must be disabled, use `--no-database-list` and force a DB:

```bash
python3 odoo-bin -d odoo_cloud --addons-path=addons,odoo/addons --no-database-list
```

## 2) Common runtime switches (feature flags + mocks)

For Cloud-agent debugging, these are the practical toggles to use immediately:

- Developer behavior / live reload:
  - `--dev=xml,reload`
- Restrict visible DBs to one:
  - `--db-filter=^odoo_cloud$`
- Disable DB listing:
  - `--no-database-list`
- Install/update selected modules quickly:
  - `-i <module_a,module_b>`
  - `-u <module_a,module_b>`
- Stop after init/update (non-interactive test runs):
  - `--stop-after-init`
- Limit workers for deterministic tests:
  - `--workers=0`

Mock/stub approach when external systems are involved:
- Prefer Odoo test doubles/patching in module tests (`odoo.tests`, monkeypatching methods/services).
- Keep HTTP side effects behind model/service methods and patch those in tests.
- Do not introduce production-only fake flags; use test context and patching in test modules.

## 3) Area-based testing workflows

### A. Core framework (`odoo/`)
Use targeted test tags and stop-after-init:

```bash
source .venv/bin/activate
python3 odoo-bin -d odoo_cloud --addons-path=addons,odoo/addons --test-enable --test-tags /base --stop-after-init --workers=0
```

When iterating on a specific test class/method:

```bash
python3 odoo-bin -d odoo_cloud --addons-path=addons,odoo/addons --test-enable --test-tags :TestClass.test_method --stop-after-init --workers=0
```

### B. Business modules (`addons/<module>` Python/XML)
Fast workflow for one module:

```bash
# 1) Apply code changes
# 2) Update module + run its tests
python3 odoo-bin -d odoo_cloud --addons-path=addons,odoo/addons -u <module_name> --test-enable --test-tags /<module_name> --stop-after-init --workers=0
```

If you only need a schema/data update smoke-check:

```bash
python3 odoo-bin -d odoo_cloud --addons-path=addons,odoo/addons -u <module_name> --stop-after-init
```

### C. Web client / JS / tours (`addons/web`, module static tests)
For tour-heavy validation, run server and execute tagged tour tests in a separate command:

```bash
python3 odoo-bin -d odoo_cloud --addons-path=addons,odoo/addons --test-enable --test-tags 'post_install,-at_install,is_tour' --stop-after-init --workers=0
```

Tip: for UI troubleshooting in browser, keep a live server with `--dev=xml,reload` and reproduce manually before running tour tags.

### D. HTTP/API behavior (`HttpCase`, controllers)
Run targeted HTTP tests by module/tag:

```bash
python3 odoo-bin -d odoo_cloud --addons-path=addons,odoo/addons --test-enable --test-tags /test_http --stop-after-init --workers=0
```

When endpoint behavior depends on host/proxy, run with explicit host/proxy config in command line or config file and re-run same tags.

## 4) Practical Cloud-agent workflow (tight loop)

Use this loop for almost every task:
1. Start from a clean branch and activate virtualenv.
2. Reproduce issue or run baseline test tags.
3. Edit minimal set of files.
4. Run narrowest possible test command (module/class/tag scoped).
5. If UI-related, run a quick manual browser check.
6. Commit/push once green, then expand test scope only if needed.

## 5) Failure triage checklist

If startup fails:
- Validate venv is active and Python deps installed.
- Check PostgreSQL reachable and DB exists.
- Re-run with explicit DB params (`--db_host`, `--db_user`, etc.).
- Ensure `--addons-path=addons,odoo/addons` is present.

If tests fail unexpectedly:
- Force deterministic mode: `--workers=0`.
- Re-run with narrower `--test-tags` to isolate.
- Use fresh database for flaky stateful tests:
  - `createdb odoo_cloud_tmp`
  - run tests with `-d odoo_cloud_tmp`

## 6) How to maintain this skill (runbook capture)

Update this skill whenever you discover a new reliable trick:
1. Add the exact command (copy/paste ready).
2. Place it in the correct area section (`Core`, `Business modules`, `Web`, `HTTP/API`).
3. Add one-line “when to use” note.
4. Prefer replacing obsolete commands over adding duplicates.
5. Keep this file minimal: only proven, repeatable workflows.

Definition of done for updates:
- New instruction is executable as-is.
- It names prerequisites (DB/module/env) explicitly.
- It shortens agent setup or debugging time in practice.
