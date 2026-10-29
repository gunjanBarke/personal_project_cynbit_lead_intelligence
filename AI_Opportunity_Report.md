# AI Opportunity Report — Cynbit

## Executive summary
This proof of concept proposes a Lead Intelligence Assistant that summarizes incoming B2B inquiries, identifies likely service fit, highlights missing qualification details, assigns an explainable initial priority, and drafts follow-up emails for human review.

This is a hypothesis based on publicly described AI and automation services; it does not establish that Cynbit currently has a lead-management problem. Validate the workflow with stakeholders.

## Opportunities considered
1. **Lead qualification and follow-up (selected):** Standardize triage and reduce repetitive drafting while keeping humans in control.
2. **Intelligent document processing:** Extract fields from business documents and send uncertain results for review.
3. **Knowledge-grounded customer support:** Retrieve answers from approved documents and escalate unsupported questions.

## Why select lead qualification?
- Clear, demonstrable workflow.
- Uses Python, LLM integration, structured outputs, prompt engineering, and automation.
- Can be prototyped with synthetic data and extended to CRM integrations later.
- Human review mitigates risks from incorrect classifications or generated messages.

## Expected value to measure
- Time spent reviewing each inquiry.
- Consistency of qualification and follow-up drafts.
- Completeness of budget, timeline, and requirements.
- Percentage of drafts accepted with minor edits.

Do not claim numerical ROI until measured.

## Risks and mitigations
- Incorrect score: display rationale and validate against labeled examples.
- Hallucinated details: restrict analysis to supplied facts.
- Privacy: use synthetic data for demos and define access/retention controls.
- Bias: avoid protected traits and audit outcomes.
- Over-automation: require human approval before sending messages or changing CRM records.

## Evaluation metrics
Field extraction accuracy, service-fit classification accuracy, priority agreement with reviewers, draft factuality/usefulness, and median handling time.
