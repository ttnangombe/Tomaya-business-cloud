# Tomaya Business Cloud (v1)

This is a cloud-ready Tomaya system for client receipts + VAT working packs.

## Default login
admin / tomaya123

## Run locally
pip install -r requirements.txt
streamlit run app.py

## Deploy on Render (recommended)
Start Command:
streamlit run app.py --server.port $PORT --server.address 0.0.0.0

Env:
TOMAYA_DB_PATH=/data/tomaya_business.db
(Use Render persistent disk mounted at /data)
