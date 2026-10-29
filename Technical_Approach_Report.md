# Technical Approach Report — Cynbit Lead Intelligence Assistant

## Architecture
Streamlit UI → input validation/normalization → lead analysis → service-fit categorization and scoring → dashboard → human-reviewed draft / CSV export.

Two modes:
- Rule-based mode: deterministic and works without an API key.
- Optional Groq mode: LLM returns structured JSON for summary, requirements, missing fields, next step, and email draft. Rule-based analysis is the fallback if the LLM call fails.

## Model choice
No predictive model is trained because no labeled Cynbit lead history was provided. Initial priority is a transparent heuristic. Optional LLM inference helps interpret text but is not ground truth. A supervised model should be considered only if representative, appropriately consented labeled data is available.

## Data pipeline
1. Accept form fields or CSV rows.
2. Normalize empty/missing values.
3. Analyze message, requirements, budget, and timeline.
4. Produce service fit, score, rationale, missing fields, and suggested next step.
5. Display and export results.

## Prompt design and guardrails
The system prompt requires JSON output, use of supplied facts only, explicit missing-information reporting, no inference from protected traits, and draft-only email generation. Production work should add schema validation, rate limits, redacted logging, prompt-injection tests, and monitoring.

## Illustrative scoring
Urgency up to 30; explicit numeric budget 25; buying readiness 20; specific request 15; detailed message 10. Score capped at 100. High >=60, Medium >=30, Low <30. These are assumptions for demonstration and require calibration.

## Evaluation plan
Use 20–30 manually labeled synthetic examples. Measure field extraction accuracy, service-fit accuracy, priority agreement, draft factuality/usefulness, failure handling, and time per lead. Report actual results only after testing.

## Execution plan
1. Validate the workflow with stakeholders.
2. Create labeled examples and a baseline.
3. Test prompts and scoring thresholds.
4. Pilot with human review and approved data.
5. Consider CRM/API integration after privacy, security, and business approval.

## Limitations
Prototype only. It is not a trained sales prediction model, does not send emails, does not modify CRM records, and has no measured business impact. No private Cynbit data was available.
