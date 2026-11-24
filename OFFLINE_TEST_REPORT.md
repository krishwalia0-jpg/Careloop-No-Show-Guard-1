# Offline test results — simulated, not API evidence

Task 1.5: Eight illustrative temperature fixtures in clinics_enriched_mock.csv. Actual temperatures remain unknown; canonical weather file retains NULLs.

Task 4.1: N001 fixture: {"root_cause": "forgot_or_no_reminder", "summary": "Patient reports no reminder and forgetting the visit.", "recommended_action": "Confirm contact details, send reminder, offer rebooking.", "confidence": 0.95}

Task 4.2: Nine fixtures passed Pydantic; N004 skipped. Confidence values are arbitrary test inputs, not model estimates.

Task 4.3: Deliberate validation failures:
1 validation error for FollowupInsight
confidence
  Input should be less than or equal to 1 [type=less_than_equal, input_value=1.7, input_type=float]
    For further information visit https://errors.pydantic.dev/2.13/v/less_than_equal
1 validation error for FollowupInsight
recommended_action
  Field required [type=missing, input_value={'root_cause': 'forgot_or...t.', 'confidence': 0.95}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.13/v/missing

Prompt comparison fixtures (not actual prompt performance):

|Note|Prompt|Category|Valid|
|---|---|---|---|
|N007|V1|forgot|False|
|N007|V2|forgot_or_no_reminder|True|
|N009|V1|unreachable|False|
|N009|V2|other|True|

V2 fixtures demonstrate allowed categories; no empirical prompt comparison is possible offline. Actual API calls: 0.

Task 4.4: Manual labels joined to actual reminder records:
```
reminder_sent          No  Yes
root_cause                    
cost_or_fee             0    1
distance_or_transport   1    1
forgot_or_no_reminder   2    0
illness_or_emergency    0    1
other                   1    1
work_or_schedule        1    1
```
No reminder: 5 of 10.
