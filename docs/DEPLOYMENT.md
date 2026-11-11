# Run and deploy FundLens India

## Local Python 3.11+

```bash
git clone https://github.com/abhinavgautam121/FundLens-India.git
cd FundLens-India
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
streamlit run app.py
```

Open http://localhost:8501. Demo generation and schema creation run automatically. There
are no API keys and no dependency on an external data site being available at launch.
On Windows use `.venv\Scripts\activate` instead of `source .venv/bin/activate`, and copy the
environment example with your shell's copy command. Run commands from the repository root.

For exact versions used during validation, `requirements-lock.txt` captures the Python 3.12
environment. `requirements.txt` supports Python 3.11+ with compatible versions resolved by pip.

## Streamlit Community Cloud

1. Push the repository to GitHub.
2. In https://share.streamlit.io/, select **Create app**, the repository, branch `main`, and
   entry point `app.py`. Select Python 3.11 or 3.12 in advanced settings.
3. Deploy. The public demo uses generated fictional data and no secret values.
4. Test all sidebar pages and verify the DEMO DATA disclosure is visible.

SQLite on Community Cloud is ephemeral: uploaded data can disappear after a restart or
redeployment. Treat Community Cloud as a demonstration host. Imported data is instance-wide,
not private per visitor. For a private research workspace, configure host access controls
and persistent storage. Do not upload sensitive user data to a shared public deployment.

No production deployment is claimed by this repository. Deployment requires the owner's
Streamlit hosting account; local execution and tests are independent of hosting credentials.

## Docker

```bash
docker build -t fundlens-india .
docker run --rm -p 8501:8501 fundlens-india
```

To retain SQLite files across container restarts, mount a writable data directory:

```bash
mkdir -p data
# Container user UID 10001 needs write permission on this directory.
docker run --rm -p 8501:8501 -v "$(pwd)/data:/app/data" fundlens-india
```

The image runs as a non-root user and includes an HTTP health check. The Dockerfile is
provided for reproducibility; consult `docs/VALIDATION.md` for what was actually executed.
No secrets or local database files are copied into the image.

## Environment and operations

| Variable | Default | Purpose |
|---|---|---|
| DATABASE_URL | sqlite:///data/fundlens.db | Uploaded dataset |
| DEMO_DATABASE_URL | sqlite:///data/fundlens-demo.db | Separate synthetic dataset |
| RISK_FREE_RATE | 0.06 | Initial annual research assumption, adjustable in UI |

The two database URLs must differ. Back up local SQLite files when the application is stopped
or use SQLite's backup API. The application uses one initial schema; future upgrades require
explicit migrations, not deletion of imported data. PostgreSQL needs a driver installation
and further runtime verification. `.env`, raw uploads and local databases are Git-ignored.

The upload limit is 20 MB and imports are manually initiated. CSV downloads escape formula
prefixes on text cells. Logging includes import counts/status and avoids file contents.
