# PLFS Field Operations Dashboard

Real-time Para Data Analysis dashboard built with Plotly Dash.

## Files needed

| File | Purpose |
|------|---------|
| `dashboard_v1.py` | Main Dash application |
| `PLFS_FSU_Completion_History_Summary_Analyzed.xlsx` | Source data |
| `requirements.txt` | Python dependencies |
| `Procfile` | Tells Railway/Render how to start the app |

## Local development

```bash
pip install -r requirements.txt
python dashboard_v1.py
# Open http://127.0.0.1:8050
```

## Deploy to Railway (recommended)

1. Push this repo to GitHub
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub repo
3. Select this repo — Railway reads the `Procfile` automatically
4. App goes live at a public URL in ~2 minutes

## Deploy to Render (alternative)

1. Go to [render.com](https://render.com) → New → Web Service
2. Connect GitHub repo
3. Set **Start Command**: `gunicorn dashboard_v1:server`
4. Deploy

## Update data

To update the dashboard data:
1. Replace `PLFS_FSU_Completion_History_Summary_Analyzed.xlsx` with the new file
2. `git add . && git commit -m "update data" && git push`
3. Railway/Render auto-redeploys within ~1 minute
