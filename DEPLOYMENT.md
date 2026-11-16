# FairGig AI: multi-service Vercel deployment

This repository is configured as one Vercel project with two services. The
React SPA is built from `frontend`; the FastAPI app is built from the repository
root. Vercel routes `/api` and `/api/*` to FastAPI and all other paths to the
frontend. The React client uses relative `/api/...` URLs.

## What is hosted where

- **GitHub:** source, CSV seed data, and existing trained model artifacts.
- **Vercel Hobby:** the public `frontend` Vite service and public `app`
  FastAPI service share one project URL.
- **Supabase Free:** Postgres persistence. SQLite is retained only for local
  development because Vercel function filesystems are not persistent.

The frontend service calls the API through the public same-origin `/api` route.
There is no service binding: browser-side requests cannot use Vercel's
server-function-only bindings, and the FastAPI service does not call the
frontend service. Do not configure a `VITE_API_URL`.

## Vercel Hobby fit (checked 16 November 2026)

Vercel's current [Function limits](https://vercel.com/docs/functions/limitations)
document the following Fluid Compute limits for Hobby:

- **Memory:** up to 2 GB.
- **Maximum duration:** 300 seconds.
- **Python function bundle:** up to 500 MB uncompressed.
- **Large functions:** up to 5 GB is documented as Beta; this deployment does
  not rely on that option.
- **Fluid Compute:** enabled by default for new projects; it allows warm
  function instances to process later requests.

The original pinned dependency set expanded to 831.57 MiB on Linux/Python 3.12,
which matched the reported serverless bundle failure. The app service now uses
the separately pinned [requirements-vercel.txt](./requirements-vercel.txt) and
a custom install command. CatBoost is installed with `--no-deps` because the
wheel declares plotting and notebook packages that are not used for inference;
its NumPy, SciPy, Pandas, and `six` runtime dependencies are installed
explicitly. Pandas remains necessary because CatBoost's native extension
imports it when loading; the backend itself no longer uses Pandas for data
processing. The install step removes CatBoost's notebook widget files, the
Pandas test suite, and SciPy subpackages outside `_lib` and `sparse`. A
deployment-equivalent import and inference check passed with the pruned
packages and without sklearn, plotting, notebook, or Google SDK packages.

The Gemini integration now uses the REST API through `httpx`, avoiding the
Google SDK's large API-client and gRPC dependency tree. Backend feature building,
seeding, and fairness aggregation use the standard library and NumPy instead of
Pandas. The original HistGradientBoosting estimator is retained in
`models/all_trained_models.joblib`; the checked-in 0.37 MiB JSON inference
artifact is exported from that estimator and scored by a compact pure-Python
tree evaluator. A test compares its scores with the original estimator to a
1e-12 absolute tolerance. The original CatBoost model and ensemble weights are
still loaded and scored by CatBoost.

An audit of the pinned official PyPI Linux CPython 3.12 wheels, after applying
the configured pruning, measured 435.65 MiB of runtime packages. The selected
backend, CSV, and model files add 3.98 MiB, for an estimated uncompressed
function bundle of 439.63 MiB (about 460.98 MB decimal), approximately 39 MB
below a 500 MB limit. `vercel.json` scopes model/data inclusion and excludes
the frontend, documentation, tests, local SQLite database, and original HGB
training artifact from the Python function. This is a package-and-file build
equivalent, not a live Vercel deployment measurement; verify the next Vercel
build output before treating the production deployment as successful. The
5-GB large-function option is Beta and is not assumed here.

Function request/response payload limits still apply; the app's current
dashboard, paginated APIs, and CSV exports are intended for small interactive
requests, not uploading large datasets. Vercel documents a 4.5 MB maximum for
request and response bodies (except streamed responses).

Both deployed model components are loaded on first model-status or inference
use and reused in a warm Python process. Cold instances still pay for Python
and native-library imports and loading the CatBoost artifact. Fluid Compute
reuse is opportunistic, not a persistence or uptime guarantee; no keep-alive
pings are used. The first database initialization also seeds demo records from
the included CSV files.

## 1. Create the persistent database

1. Create a free Supabase project.
2. In **Connect**, choose the **Session pooler** connection string and copy its
   URI. Do not use the frontend or put it in a `VITE_*` variable.
3. Keep the Supabase database password private. The application creates its
   tables and seeds the demo data on first startup.

Supabase currently documents a 500 MB database limit on Free, and free projects
can pause after one week without activity. Resume the project in Supabase if
the first API request later fails after a long inactive period.

There is no end-user authentication in this demo. The API can create tasks,
workers, and allocations, so treat the public deployment as a demonstration
application and do not load real worker or customer data. No service-role key is
needed: the server connects directly to Postgres. Add authentication and
per-user authorization before using this app for private or production data.

## 2. Create and push the GitHub repository

Create an empty repository on GitHub (do not add a README or license there), then
run these commands in PowerShell from the project directory. Replace the
placeholder with your GitHub account or organization:

```powershell
git init -b main
git add .
git status --short
git diff --cached --check
# Review the staged filenames and verify no .env or credentials are staged.
git commit -m "Prepare FairGig AI for Vercel"
git remote add origin https://github.com/<GITHUB-OWNER>/FairGig-AI.git
git push -u origin main
```

`.gitignore` excludes environment files, the local SQLite database, Python
bytecode, Vercel metadata, frontend dependencies, and build output. Commit the
trained model artifacts and source CSV files: the backend needs them to perform
real inference and to seed the database. The workspace did not contain a Git
repository when this setup was prepared, so no existing Git history was
available to scan for previously committed secrets.

## 3. Import into Vercel

1. Sign in to Vercel and choose **Add New → Project**.
2. Import the GitHub repository.
3. Set **Root Directory** to the repository root (not `frontend` or `backend`).
4. The root `vercel.json` defines two services: `app` (FastAPI, root `.`) and
   `frontend` (Vite, root `frontend`). It routes `/api` and `/api/*` to `app`
   and all other paths to `frontend`. Do not add a rewrite to an external
   backend origin.
5. `pyproject.toml` selects Python 3.12 and the FastAPI entrypoint. The app
   service's `installCommand` installs the small, pinned runtime manifest and
   then installs only CatBoost's inference runtime, avoiding its unused plotting
   and widget dependencies. Local development uses the full
   [requirements.txt](./requirements.txt); regenerate the compact HGB artifact
   after changing the trained estimator with
   `python backend/scripts/export_hgb_inference.py`.
6. Under **Settings → Environment Variables**, add:
   - `DATABASE_URL`: the Supabase **Session pooler** URI, server-side only.
   - `GEMINI_API_KEY` (optional): the backend uses Gemini `gemini-3.6-flash`
     when configured. If it is missing or a request fails, deterministic
     explanations remain available without blocking allocation.
   Set variables for **Production** (and Preview only if you intend preview
   deployments to share the same database).
7. Deploy. Name the project `fairgig-ai` if that Vercel project/domain name is
   available. Vercel domain availability cannot be confirmed until it is
   assigned in your account.

The Python function refuses to start on Vercel if `DATABASE_URL` is missing;
this avoids silently writing to ephemeral SQLite storage. Environment secrets
belong in Vercel's dashboard, not in this repository or chat.

## 4. Verify the deployment

After deployment, replace `<DEPLOYMENT>` with the assigned Vercel URL:

- Open `https://<DEPLOYMENT>/dashboard`, then refresh the page directly.
- Open `https://<DEPLOYMENT>/api/health`; it should return HTTP 200, report the
  database connected, and report both trained model artifacts operational.
- Open `/api/ai/status` for safe backend provider state. It does not make an
  external request; Gemini availability updates when an explanation request
  succeeds or falls back.
- Open `/api/tasks?page=1&limit=1` and `/api/workers?page=1&limit=1`; each should
  return a page of demo records.
- In the app, preview an allocation and run the multi-agent workflow. Confirm
  the returned scores include the ensemble prediction and WAFR fields.
- Open Fairness, Model Insights, History, Reports, and Settings. Try the
  history/report endpoints and download a report.

Do not announce a successful deployment until the actual public URL and these
checks have been tested. This checkout has no local Vercel project link or authenticated CLI session.
Use the existing GitHub-to-Vercel integration to run and inspect the deployment
build after pushing changes.

## Local checks

From the project root:

```powershell
python -m pip install -r requirements.txt
Push-Location .\frontend
npm ci
npm run build
Pop-Location
```

For local development, set `FAIRGIG_DB_PATH` if you want to use a disposable
SQLite database, seed it from the `backend` directory, then run FastAPI and
Vite using the existing Windows startup scripts. The Vite proxy is only for
local development; production requests remain same-origin.

Copy `.env.example` to a root `.env` for local server-side configuration, then
replace its placeholders. The backend loads that file with `python-dotenv`;
`.env` is ignored by Git. Never put `GEMINI_API_KEY` in a `VITE_*` variable or
send it from the browser.

## References

- [Vercel FastAPI deployment](https://vercel.com/docs/frameworks/backend/fastapi)
- [Vercel Python runtime](https://vercel.com/docs/functions/runtimes/python)
- [Vercel Function limits](https://vercel.com/docs/functions/limitations)
- [Vercel Function duration](https://vercel.com/docs/functions/configuring-functions/duration)
- [Supabase connection strings](https://supabase.com/docs/guides/database/connecting-to-postgres)
