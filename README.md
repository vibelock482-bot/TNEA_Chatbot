# TNEA College Recommendation Chatbot

Flask + SQLite chatbot. Recommends colleges as Safe / Target / Ambitious from historical TNEA cutoffs.

## IMPORTANT: data
`data/colleges.csv` ships with only 3 real college names and **no cutoff values**, because cutoffs must come from official
TNEA data. Fill it in with real data, one row per college + branch + community + year:

    college_code,college_name,district,college_type,branch,community,cutoff,year

- community: OC, BC, BCM, MBC, SC, SCA, ST
- college_type: Government, Government Aided, Self-Financing, University
- Leave `cutoff` blank when data is unavailable (the college is then never recommended).
- Use the official cutoff/allotment data from tneaonline.org and verify it before publishing.

## Run locally
    pip install -r requirements.txt
    python app.py          # http://localhost:5000
    python -m pytest -q tests

## Update data without code
Set env var `ADMIN_TOKEN`, open `/admin`, upload a CSV (replaces all data).
Also update `data/colleges.csv` in the repo, because Render's free disk resets on restart and the DB is rebuilt from that file.

## Deploy on Render
Push to GitHub, create a Web Service (or use render.yaml). Build: `pip install -r requirements.txt`. Start: `gunicorn app:app`.
Set `ADMIN_TOKEN` in the dashboard.

## Tuning
Edit the thresholds in `config.py` (SAFE_MIN, TARGET_MIN, AMBITIOUS_MIN).
