import os, json, re
from datetime import datetime
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
load_dotenv()

try:
    from groq import Groq
except ImportError:
    Groq = None

APP_TITLE = "Cynbit Lead Intelligence Assistant"
DEFAULT_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
st.set_page_config(page_title=APP_TITLE, page_icon="🧠", layout="wide")
st.title("🧠 Cynbit Lead Intelligence Assistant")
st.caption("PoC for lead analysis, explainable prioritization, and human-reviewed follow-up drafts.")

with st.sidebar:
    st.header("Settings")
    use_llm = st.toggle("Use Groq LLM for analysis", value=bool(os.getenv("GROQ_API_KEY")))
    model_name = st.text_input("Groq model", value=DEFAULT_MODEL)
    st.caption("Without a configured API key, the app uses rule-based analysis.")
    st.divider()
    st.markdown("**Privacy note**")
    st.write("Use synthetic/demo data. If Groq is enabled, lead text is sent to the configured LLM API.")

SERVICES = {
    "AI / ML solution": ["machine learning", "predict", "prediction", "computer vision", "classification", "model"],
    "Generative AI / RAG": ["rag", "llm", "generative ai", "chatbot", "knowledge base", "document question", "assistant"],
    "AI automation / agents": ["automation", "agent", "workflow", "automate", "crm", "follow-up", "follow up"],
    "AI voice agent": ["voice", "phone call", "call agent", "voice bot", "speech"],
    "Document processing": ["document", "invoice", "extract", "pdf", "contract", "ocr"]
}

def safe_float(value):
    try:
        return float(str(value).replace(",", "").replace("$", "").replace("₹", "").strip())
    except (TypeError, ValueError):
        return None

def detect_service(text):
    low = (text or "").lower()
    scores = {s: sum(term in low for term in terms) for s, terms in SERVICES.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] else "Needs discovery"

def make_email_draft(lead, service, priority):
    name = str(lead.get("contact_name") or "there").strip()
    company = str(lead.get("company") or "your team").strip()
    message = str(lead.get("message") or "").strip()
    opener = f"Thank you for reaching out about {service.lower()}."
    if message:
        opener += f" I understand you're exploring: {message[:240]}"
    return (f"Subject: Next steps for your AI initiative\n\nHi {name},\n\nThank you for your interest. {opener}\n\n"
            f"It would be helpful to learn more about your goals, current workflow, timeline, and success criteria "
            f"so we can recommend a suitable approach for {company}.\n\nWould you be available for a brief discovery call? "
            f"We can discuss your requirements and determine the most useful next step.\n\nBest regards,\nCynbit Team")

def rule_based_analysis(lead):
    text = " ".join(str(lead.get(k, "")) for k in ["message", "company", "requirements", "budget", "timeline"])
    low = text.lower()
    budget = safe_float(lead.get("budget"))
    score, reasons = 0, []
    if any(w in low for w in ["urgent", "asap", "immediately", "this week", "within 7 days"]):
        score += 30; reasons.append("Urgent timeline mentioned (+30)")
    elif any(w in low for w in ["this month", "within 30 days", "next month"]):
        score += 20; reasons.append("Near-term timeline mentioned (+20)")
    elif any(w in low for w in ["quarter", "3 months", "three months"]):
        score += 10; reasons.append("Defined medium-term timeline (+10)")
    if budget is not None and budget > 0:
        score += 25; reasons.append("Budget provided (+25)")
    elif any(w in low for w in ["budget", "$", "₹", "usd", "inr"]):
        score += 10; reasons.append("Budget needs confirmation (+10)")
    if any(w in low for w in ["decision maker", "approved", "approval", "ready to start", "ready to proceed"]):
        score += 20; reasons.append("Buying readiness/authority signaled (+20)")
    if any(w in low for w in ["demo", "pilot", "proposal", "quote", "pricing", "estimate"]):
        score += 15; reasons.append("Specific next-step request (+15)")
    if len(str(lead.get("message") or "").strip()) >= 80:
        score += 10; reasons.append("Detailed inquiry supplied (+10)")
    score = min(score, 100)
    priority = "High" if score >= 60 else "Medium" if score >= 30 else "Low"
    service = detect_service(text)
    next_step = {
        "High": "Respond promptly, validate scope and budget, and offer a discovery call or demo.",
        "Medium": "Ask one or two qualifying questions and suggest a short discovery call.",
        "Low": "Send a helpful introduction and clarify needs, timing, and budget."
    }[priority]
    missing = [label for key, label in [
        ("company", "Company name"), ("budget", "Budget"), ("timeline", "Timeline"), ("contact_email", "Contact email")
    ] if not str(lead.get(key, "")).strip()]
    req_text = str(lead.get("requirements") or lead.get("message") or "")
    requirements = [x.strip() for x in re.split(r"[.;\n]", req_text) if x.strip()][:5]
    return {
        "lead_summary": (str(lead.get("message") or "No message provided").strip())[:500],
        "service_fit": service, "priority_score": score, "priority": priority,
        "key_requirements": requirements, "missing_information": missing,
        "recommended_next_step": next_step,
        "scoring_reasons": reasons or ["No strong buying signals detected; gather more information."],
        "follow_up_email": make_email_draft(lead, service, priority)
    }

def llm_analysis(lead, model):
    if Groq is None:
        raise RuntimeError("The groq package is not installed.")
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not configured.")
    client = Groq(api_key=api_key)
    system = """You are a careful B2B lead qualification assistant. Use only supplied information.
Return valid JSON keys: lead_summary (string), service_fit (string), priority_score (integer 0-100),
priority (High/Medium/Low), key_requirements (array), missing_information (array),
recommended_next_step (string), scoring_reasons (array), follow_up_email (string).
Use urgency, explicit budget, buying readiness, specific request, and completeness. Do not infer protected traits
or make assumptions from names, gender, ethnicity, age, or location. State missing information. Draft only; never claim an email was sent."""
    user = {k: str(lead.get(k, "")) for k in ["company","contact_name","contact_email","message","requirements","budget","timeline"]}
    response = client.chat.completions.create(
        model=model, temperature=0.2, response_format={"type":"json_object"},
        messages=[{"role":"system","content":system},{"role":"user","content":json.dumps(user, ensure_ascii=False)}]
    )
    result = json.loads(response.choices[0].message.content)
    result["priority_score"] = max(0, min(100, int(result.get("priority_score", 0))))
    result.setdefault("priority", "Medium")
    for key in ["scoring_reasons","key_requirements","missing_information"]:
        if not isinstance(result.get(key), list): result[key] = []
    result.setdefault("follow_up_email", make_email_draft(lead, result.get("service_fit","AI solution"), result["priority"]))
    return result

def normalize_lead(raw):
    keys = ["company","contact_name","contact_email","message","requirements","budget","timeline"]
    return {k: ("" if pd.isna(raw.get(k, "")) else str(raw.get(k, "")).strip()) for k in keys}

tab_one, tab_batch, tab_about = st.tabs(["Analyze a lead", "Batch CSV analysis", "About this PoC"])
with tab_one:
    left, right = st.columns(2)
    with left:
        st.subheader("Lead details")
        with st.form("lead_form"):
            company = st.text_input("Company", placeholder="Northstar Logistics")
            contact_name = st.text_input("Contact name (optional)")
            contact_email = st.text_input("Contact email (optional)")
            message = st.text_area("Lead message *", height=130, placeholder="We need an AI assistant to answer questions from our internal documents...")
            requirements = st.text_area("Requirements (optional)", height=80)
            budget = st.text_input("Budget (optional)", placeholder="5000")
            timeline = st.text_input("Timeline (optional)", placeholder="Within 30 days")
            submitted = st.form_submit_button("Analyze lead", type="primary")
    if submitted:
        if not message.strip():
            st.error("Please enter the lead message.")
        else:
            lead = normalize_lead(locals())
            # Explicitly construct the submitted record rather than relying on Streamlit internals.
            lead = normalize_lead({"company":company,"contact_name":contact_name,"contact_email":contact_email,
                                   "message":message,"requirements":requirements,"budget":budget,"timeline":timeline})
            with st.spinner("Analyzing lead..."):
                try:
                    result = llm_analysis(lead, model_name) if use_llm else rule_based_analysis(lead)
                except Exception as exc:
                    st.warning(f"LLM analysis failed; showing rule-based result instead. Details: {exc}")
                    result = rule_based_analysis(lead)
                st.session_state["last_result"] = result
                st.session_state["last_lead"] = lead
                st.session_state["last_timestamp"] = datetime.now().isoformat(timespec="seconds")
    result = st.session_state.get("last_result")
    if result:
        with right:
            st.subheader("Analysis results")
            a, b = st.columns(2)
            a.metric("Priority score", f'{result.get("priority_score",0)}/100')
            b.metric("Priority", result.get("priority","—"))
            st.write("**Service fit:**", result.get("service_fit","Needs discovery"))
            st.write("**Summary:**", result.get("lead_summary",""))
            st.write("**Recommended next step:**", result.get("recommended_next_step",""))
            st.write("**Key requirements**")
            for item in result.get("key_requirements", []): st.write(f"- {item}")
            st.write("**Information to confirm**")
            st.write(", ".join(result.get("missing_information", [])) or "No obvious missing fields detected.")
            st.write("**Scoring rationale**")
            for item in result.get("scoring_reasons", []): st.write(f"- {item}")
        st.subheader("Follow-up email draft — review before sending")
        st.text_area("Editable draft", value=result.get("follow_up_email",""), height=220, key="email_draft")
        st.download_button("Download analysis JSON", data=json.dumps(result, indent=2), file_name="lead_analysis.json", mime="application/json")

with tab_batch:
    st.subheader("Analyze multiple leads")
    st.write("Upload CSV with `message` and optional columns: company, contact_name, contact_email, requirements, budget, timeline.")
    sample_path = os.path.join(os.path.dirname(__file__), "data", "sample_leads.csv")
    if os.path.exists(sample_path):
        with open(sample_path, "rb") as f:
            st.download_button("Download sample CSV", data=f.read(), file_name="sample_leads.csv", mime="text/csv")
    uploaded = st.file_uploader("Upload leads CSV", type=["csv"])
    if uploaded:
        try:
            df = pd.read_csv(uploaded).fillna("")
            if "message" not in df.columns:
                st.error("CSV must include a 'message' column.")
            elif st.button("Analyze CSV"):
                rows = []
                progress = st.progress(0)
                for i, (_, row) in enumerate(df.iterrows()):
                    lead = normalize_lead(row.to_dict())
                    try: out = llm_analysis(lead, model_name) if use_llm else rule_based_analysis(lead)
                    except Exception: out = rule_based_analysis(lead)
                    rows.append({**lead, "priority_score":out.get("priority_score",0), "priority":out.get("priority","Medium"),
                                 "service_fit":out.get("service_fit",""), "recommended_next_step":out.get("recommended_next_step",""),
                                 "missing_information":"; ".join(out.get("missing_information",[])),
                                 "follow_up_email":out.get("follow_up_email","")})
                    progress.progress((i+1)/max(len(df),1))
                out_df = pd.DataFrame(rows)
                st.dataframe(out_df, use_container_width=True)
                st.download_button("Download analyzed leads CSV", data=out_df.to_csv(index=False).encode("utf-8"),
                                   file_name="analyzed_leads.csv", mime="text/csv")
        except Exception as exc:
            st.error(f"Could not read CSV: {exc}")

with tab_about:
    st.subheader("What this proof of concept demonstrates")
    st.markdown("""
- Lead-message summary and service-fit categorization
- Explainable rule-based prioritization or optional LLM structured analysis
- Missing-information detection
- Human-reviewed follow-up email drafts
- Batch CSV processing and export

**Limitations**
- The score is a demo heuristic, not a trained predictive model or validated sales forecast.
- No emails are sent and no CRM is modified.
- Use synthetic data in the demo; evaluate against manually labeled examples before real-world use.
""")
