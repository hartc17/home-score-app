# Claude Code Instructions - HouseFlavor

## Documentation rule (mandatory)

After any phase completion or extensive code changes, always update all relevant docs before committing:

| Doc | Update when |
|---|---|
| `README.md` | Any new file, endpoint, dependency, setup step, or phase status change |
| `docs/architecture.md` | Any change to data flow, layers, modules, or DB schema |

Check every doc for stale references.
Do not leave forward-looking language in docs after the thing has been built.

## Project conventions

- **Python 3.12**, venv at `.venv/`. Always activate with `source .venv/bin/activate`.
- **Node 20+**, use `npm` workspaces.
- **Run Python tests** with `pytest` from the project root.
- **Run web tests** with `npm test` from `apps/web`.
- All tests must pass before committing.
- **Commit style**: `Phase N: short description` matching the existing log.

## General principles

- Never use the em dash "-". Use plain dash "-" instead.
- When writing commit messages, NEVER auto-add your agent name as co-author.
- Never manually modify CHANGELOG.md files or any files marked as auto-generated.
- When writing or substantially editing long Markdown files, put each full sentence on its own line.
  Preserve normal Markdown structure, but avoid wrapping multiple sentences onto one physical line.
- When making technical decisions, do not give much weight to development cost.
  Instead, prefer quality, simplicity, robustness, scalability, and long term maintainability.
- When doing bug fixes, always start with reproducing the bug in an E2E setting as closely aligned with how an end user would experience it.
- When end-to-end testing a product, be picky about the UI you see and be obsessed with pixel perfection.
  If something clearly looks off, even if it is not directly related to what you are doing, try to get it fixed alongside the main task.
- Apply that same high standard to engineering excellence: lint, test failures, and test flakiness.
  If you see one, even if it is not caused by what you are working on right now, still get it fixed.

## Code quality

- **No comments that describe what the code does** - only add a comment when the WHY is non-obvious (hidden constraint, workaround for a specific bug, subtle invariant).
  Well-named identifiers document themselves.
- **No dead code** - remove unused functions, imports, and variables rather than commenting them out.
- **No speculative abstractions** - don't generalise until there are at least three concrete cases.
- **No error handling for impossible cases** - trust internal code and framework guarantees.
  Only validate at system boundaries (user input, external APIs).
- **Type annotations on all function signatures** - use Python 3.12 union syntax (`X | None`) not `Optional[X]`.
- **Pydantic for all API boundaries** - never accept or return raw `dict` from an endpoint without a schema.

## Testing

- **Every new module gets a test file** - no untested public functions.
- **Tests must not hit the network or a real DB** - mock HTTP with `pytest-mock`; use in-memory SQLite or mock the session for DB-touching code.
- **Test the behaviour, not the implementation** - assert on return values and side effects.
- **Fixture files live in `tests/fixtures/`** - synthetic data used across multiple test files go there, not duplicated per file.
- **Name tests as `test_<thing>_<condition>_<expected>`**.

## Git

- **Work off `main`** - commit and push changes directly to `main`.
- **Never commit with `--no-verify`** - if a hook fails, fix the underlying issue.
- **Never force-push `main`**.
- **One logical change per commit** - don't bundle unrelated fixes.
- **Always run tests immediately before committing**.
- **After any set of changes**: commit and push to `main`.

## FastAPI patterns

- **Routers, not monolithic `app.py`** - each resource group gets its own file under `services/scoring/app/api/routes/`.
- **`HTTPException` for client errors, unhandled exceptions for server errors**.
- **Response models declared on every endpoint** - never rely on implicit serialisation of arbitrary dicts.

## Dependencies

- Pin new Python dependencies in `pyproject.toml` with a minimum version (`>=`).
- Pin new JS dependencies with exact versions in `package.json`.
- Don't add a dependency for something in the standard library or already available.

## Architecture in one paragraph

A user answers image-only forced-choice questions; the app infers a personal taste **rubric** (directional preferences + category weights).
They optionally complete a **gates** step (budget, district, beds/baths) that adds hard constraints to the rubric.
They paste listing URLs; the **scoring service** (FastAPI) fetches the page, extracts photos, sends them to Claude vision (preference-neutral JSON observations), then applies the rubric via deterministic match x weight math to produce a 0-100 score, verdict, and due-diligence checklist.
The same listing scores differently for different users - that is the product.

## Phase status

| Phase | Status |
|---|---|
| A | 🔨 Quiz -> Rubric (client-side inference, anonymous persistence). Core built; share-card image export and the per-option photo swap seam done; curated photo bank pending on content licensing. |
| B | 🔨 Gates + anonymous persistence + merge. Gates form, rubric merge, and versioned server-side persistence (anonymous-id keyed) done; magic-link account claim deferred by design. |
| C | 🔨 Scoring service. Deterministic core + style-affinity done; scoring-contract.md written; Claude vision analyzer built (gated on ANTHROPIC_API_KEY), triage/resize hardening left. |
| D | 🔨 Persistence + comparison view. Listing/photo-analysis/score/dd-item tables, score-run endpoint (get-or-create listing, reuse photoset-hash cache, per-rubric score), and ranked comparison view built. |
