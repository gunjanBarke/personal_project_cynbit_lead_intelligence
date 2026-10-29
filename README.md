# Cynbit Lead Intelligence Assistant

A Streamlit proof of concept for lead qualification, explainable prioritization, and human-reviewed follow-up drafting.

## Features
- Analyze a single lead or upload a CSV of leads.
- Categorize likely service fit across AI/ML, GenAI/RAG, automation, voice agents, and document processing.
- Show a heuristic priority score and rationale.
- Identify missing qualification fields.
- Draft follow-up emails for human review.
- Export results as JSON or CSV.
- Optional Groq LLM mode; deterministic rule-based mode works without an API key.

## Run on Windows PowerShell
```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```
These commands do not require activating the virtual environment.

## Optional Groq mode
Set `GROQ_API_KEY` in your environment before launching Streamlit. The `.env.example` file is a template only; this app does not automatically load `.env` files. Never commit a real API key. If the API fails, the app falls back to rules.

## CSV format
Required: `message`. Optional: `company`, `contact_name`, `contact_email`, `requirements`, `budget`, `timeline`. See `data/sample_leads.csv`.

## Scoring
Illustrative rules assign points for urgency (up to 30), numeric budget (25), buying readiness (20), a specific request (15), and a detailed message (10). High >=60, Medium >=30, Low <30. These are demonstration heuristics, not validated predictions.

## Limitations
No emails are sent and no CRM is changed. Use synthetic data. When Groq is enabled, lead text is transmitted to the configured LLM provider. Validate scores against labeled data before any operational use.
