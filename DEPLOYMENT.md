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

The included model files total about 6.2 MB, and the CSV and held-out prediction
data total about 2.5 MB. Dependencies are pinned in the root
[requirements.txt](./requirements.txt). A Python 3.12 Linux wheel audit resolved
831.6 MiB of uncompressed dependency contents, before the application and model
files; this exceeds the standard 500 MB limit. An authenticated Vercel build is
still required to determine the actual function bundle size. Do not treat
deployment as viable on Hobby unless the bundle fits the limit; the 5-GB option
is Beta and is not assumed here. Function request/response payload limits still apply; the app's
current dashboard, paginated APIs, and CSV exports are intended for small
interactive requests, not uploading large datasets. Vercel documents a 4.5 MB
maximum for request and response bodies (except streamed responses).

The model is loaded on first model-status or inference use and retained in a
warm Python process. Cold instances still pay for Python/native-library imports
and loading both existing trained models. Fluid Compute reuse is opportunistic,
not a persistence or uptime guarantee; no keep-alive pings are used. The first
database initialization also seeds demo records from the included CSV files.

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
5. `pyproject.toml` selects Python 3.12 and the FastAPI entrypoint; this matches
   the tested scikit-learn 1.6.1 model serialization and has compatible Linux
   wheels.
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
checks have been tested. This workspace has not yet been connected to GitHub,
Supabase, or an authenticated Vercel account.

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
