@echo off
cd /d "%~dp0"

echo Starting Streamlit...
start "" streamlit run app.py --server.headless true
ping 127.0.0.1 -n 3 > nul

echo Opening browser...
start "" http://localhost:8501
