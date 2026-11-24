# Manual review of the first 10 follow-up notes

**Provenance:** This is a human-style interpretation of the supplied note text, **not** a Gemini API output. Confidence scores and raw API responses are intentionally absent. It does not meet the API-execution requirement in Tasks 4.1–4.3.

## Task 4.1 — illustrative classification
N001: `forgot_or_no_reminder`. The patient reported not receiving a reminder and forgetting the appointment. This is a manual classification, not a validated Gemini call.

## Task 4.2 — first 10 notes
The attached `notes_manual_review.csv` records all 10 notes. N004 is blank and classified `other` for reporting; N009 is `other` because the patient was unreachable, not because the actual reason is known.

## Task 4.3 — validation and prompt comparison
The notebook contains Pydantic tests for confidence 1.7 and a missing `recommended_action`. The four real Gemini prompt-comparison responses for N007 and N009 remain unexecuted; no API call counts or comparison outcomes have been fabricated.

## Task 4.4 — reminder cross-tab (manual labels)

| root_cause            |   No |   Yes |
|:----------------------|-----:|------:|
| cost_or_fee           |    0 |     1 |
| distance_or_transport |    1 |     1 |
| forgot_or_no_reminder |    2 |     0 |
| illness_or_emergency  |    0 |     1 |
| other                 |    1 |     1 |
| work_or_schedule      |    1 |     1 |

Five of the ten linked bookings have `reminder_sent = No`; both manually classified `forgot_or_no_reminder` notes (N001 and N007) have `reminder_sent = No`. These ten selected notes are not representative of all bookings and cannot establish a causal reminder effect.
