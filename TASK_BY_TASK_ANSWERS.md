# CareLoop Clinics — task-by-task answer sheet

**Evidence status:** Parts 1–3 below are based on the supplied CSVs and generated outputs. Part 4 contains the exact required procedure and *manual illustrative interpretations* of the original notes, **not** fabricated Gemini API results. The Gemini experiment cannot be claimed complete without running the API. Weather enrichment also requires a live Open-Meteo connection. All code for these experiments is in the corresponding notebooks.

## Part 1 — Python & Data Foundations (26 marks)

### Task 1.1 — CSV module (5)
**Method:** Use `with open(..., newline='')` and `csv.DictReader`; print field names and row count. `parse_row` converts `age`, `fee_inr`, `prior_no_shows` to `int` and `distance_km` to `float`. Catch `ValueError` and save rejected dictionaries with `json.dump(..., indent=2)`.

**Result:** 1,020 rows; 988 accepted; 32 rejected (12 blank ages and 20 blank distances). Impossible but numeric ages remain accepted here. See `01_ingest_clean.ipynb` and `rejected_rows.json`.

### Task 1.2 — Cleaning pass 1 (5)
**Method:** Restart from original CSV using pandas; inspect `shape`, `info`, missingness, duplicate counts. Drop exact duplicate rows, strip/title-case `booking_channel`, coerce `appt_date` and parse `booked_on`, then remove missing appointment dates/statuses.

**Result:** Raw (1020,14); nulls: age 12, distance 20, status 4, appointment date 1; exact duplicates 20. Booking channels go from 16 raw spellings to App, Phone, Walk-In. Rows: 1020 → 1000 after duplicates → 990 after 6 invalid dates and 4 missing statuses.

### Task 1.3 — Cleaning pass 2 (5)
**Method:** Mark ages outside [1,100] missing, fill age with median and convert to int; fill distance with median; calculate Q1/Q3/IQR and clip distance and fees at Tukey fences, then round.

**Result:** 5 invalid ages; 17 ages missing before imputation; age median 48; distance median 8.25 km. Distance Q1 4.625, Q3 13.0, upper fence 25.5625, 26 capped. Fee Q1 500, Q3 787.5, upper fence 1218.75, 3 capped; largest rounded fee 1219 INR.

### Task 1.4 — NumPy features (4)
**Method:** `lead_days=(appt_date-booked_on).dt.days`, `no_show=(status=='No-Show').astype(int)`. Create numeric `X` from age, distance, fee and lead days. Compute `X.mean(axis=0)`, a boolean mask for lead_days > 14, and population-standard-deviation z-scores for distance with NumPy (no loops).

**Result:** 218/990 no-shows = 22.0%; lead days 1–45. Means approximately [48.17, 9.50, 635.71, 11.82]. 296/990 (29.9%) have lead_days > 14; 53 have absolute distance z-score > 2.

### Task 1.5 — Open-Meteo enrichment (3)
**Method:** For each of eight clinics, call Open-Meteo with latitude, longitude, hourly temperature_2m, forecast_days=1 and timeout=10; check HTTP 200, take hourly.temperature_2m[0], retry once on failure; otherwise store null. Export `clinics_enriched.csv`.

**Result:** The eight clinics were preserved, but the supplied offline run has missing `temp_c` for all eight. These are **not successful live readings**. A network-connected run is needed for the live-temperature acceptance criterion; do not invent temperatures.

### Task 1.6 — CSV and SQL hand-off (4)
**Method:** Sort by appointment_id, format both dates as YYYY-MM-DD, export exactly the 16 specified columns, check unique IDs and zero nulls, write eight clinic INSERT statements before 990 appointment INSERT statements.

**Result:** `appointments_clean.csv` has 990 rows × 16 columns, unique IDs, no missing fields. `load_data.sql` has 998 INSERT statements; unavailable temperatures are SQL NULL.

## Part 2 — SQL (22 marks)

**Executable answers:** `02_queries.sql` contains the full SQL for every subtask. `load_data.sql` contains the actual records. The numerical queries were verified using SQLite-compatible execution of the supplied schema and data; run in MySQL 8 for the requested MySQL duplicate-key message.

### Task 2.1 — Database and constraints (4)
Create `noshowguard`, `clinics`, and `appointments` using the supplied schema, then load `load_data.sql`. `COUNT(*)` = 8 clinics, 990 appointments; `SUM(no_show)` = 218. Inserting an appointment with an existing `appointment_id='A0001'` is rejected by the primary-key constraint. MySQL error wording is environment-dependent; do not claim a MySQL error was observed unless run there.

### Task 2.2 — Clinic rates (5)
Join appointments to clinics, group by clinic, use `HAVING COUNT(*) >= 95` and order by rate descending.

| Clinic | City | Appointments | No-shows | Rate |
|---|---|---:|---:|---:|
| Hadapsar Care Centre | Pune | 143 | 39 | 27.3% |
| Malviya Nagar Clinic | Jaipur | 142 | 38 | 26.8% |
| Kothrud Family Clinic | Pune | 160 | 36 | 22.5% |
| Vijay Nagar Clinic | Indore | 101 | 21 | 20.8% |
| Edappally Medical Centre | Kochi | 142 | 23 | 16.2% |
| Vaishali Nagar Clinic | Jaipur | 130 | 18 | 13.8% |

Without HAVING, Gomti Nagar Care Point (Lucknow) is highest at 33.3% but only 90 appointments. Sitabuldi Health Point (Nagpur) has 82 appointments and 15.9%.

### Task 2.3 — Lead-time bands (4)
Use CASE WHEN with inclusive cutoffs 7, 14 and 30, group by band and order by MIN(lead_days).

| Lead days | Appointments | No-shows | Rate |
|---|---:|---:|---:|
| 1–7 | 390 | 63 | 16.2% |
| 8–14 | 304 | 53 | 17.4% |
| 15–30 | 253 | 76 | 30.0% |
| 31+ | 43 | 26 | 60.5% |

Longer advance booking is associated with higher missed-visit risk, particularly in the 31+ group; this is not causal proof.

### Task 2.4 — Monthly CTE and LAG (4)
Create CTE `monthly` with `SUBSTR(appt_date,1,7)`, appointments and rounded rate; calculate this month's rate minus `LAG(rate)`.

| Month | Appointments | Rate | Change (pp) |
|---|---:|---:|---:|
| 2025-01 | 157 | 24.8% | — |
| 2025-02 | 151 | 20.5% | -4.3 |
| 2025-03 | 142 | 20.4% | -0.1 |
| 2025-04 | 177 | 20.9% | +0.5 |
| 2025-05 | 198 | 23.7% | +2.8 |
| 2025-06 | 165 | 21.2% | -2.5 |

### Task 2.5 — Rank within city (5)
Use a `clinic_rates` CTE and `RANK() OVER (PARTITION BY city ORDER BY no_show_pct DESC)`; compare to overall 218/990 = 22.02% with a scalar subquery.

| City | Clinic | Rate | City rank | Versus overall |
|---|---|---:|---:|---|
| Indore | Vijay Nagar | 20.8% | 1 | below |
| Jaipur | Malviya Nagar | 26.8% | 1 | above |
| Jaipur | Vaishali Nagar | 13.8% | 2 | below |
| Kochi | Edappally | 16.2% | 1 | below |
| Lucknow | Gomti Nagar | 33.3% | 1 | above |
| Nagpur | Sitabuldi | 15.9% | 1 | below |
| Pune | Hadapsar | 27.3% | 1 | above |
| Pune | Kothrud | 22.5% | 2 | above |

## Part 3 — Machine learning (30 marks)

**Executable answers:** `03_model.ipynb` has each task separately. The test set was used for reporting, not for selecting the model or threshold.

### Task 3.1 — Features, split, baseline (5)
Use age, distance_km, fee_inr, lead_days, prior_no_shows, binary reminder_sent, and one-hot encoded booking_channel and visit_type. Exclude IDs, clinic, gender, dates and status. There are 11 features. Split with `test_size=0.2, random_state=42` without reordering the CSV. Train = 792, test = 198, test no-shows = 49. Always predicting Attended yields 149/198 = 0.7525 accuracy.

### Task 3.2 — Logistic regression (6)
Fit StandardScaler on training only; LogisticRegression(max_iter=1000). Test accuracy ≈0.788; precision ≈0.63, recall ≈0.35, F1 ≈0.45, ROC-AUC ≈0.789; confusion matrix ≈[[139,10],[32,17]]. `reminder_sent` has the strongest negative scaled coefficient (about -0.58). Its standardized odds ratio is exp(-0.58) ≈0.56 per standard deviation, **not** the No→Yes change. Dividing by the feature's training SD ≈0.49 gives exp(coef/scale) ≈0.31, corresponding to about 69% lower odds **associated** with a reminder holding other modeled features constant. This does not establish causation.

### Task 3.3 — Decision tree overfitting (5)
Unrestricted tree: train accuracy 1.00, test about 0.67; depth about 15. Depth-3 tree: train about 0.82, test about 0.78. The unrestricted tree fits noise and generalises worse, even below the majority-class baseline.

### Task 3.4 — Random forest (6)
100 trees, random_state=42: training accuracy 1.00, test accuracy ≈0.75, recall ≈0.31, ROC-AUC ≈0.71. Top three importances include lead_days (~0.22), age (~0.20), distance_km (~0.19); exact order can vary. Descriptive test comparison: logistic regression has the strongest observed ROC-AUC, but formal model selection uses training CV only.

### Task 3.5 — CV selection, threshold, held-out test (8)
GridSearchCV forest: n_estimators=[100,200], max_depth=[3,5,8], cv=5, scoring=roc_auc; best training CV AUC ≈0.767. Compare training CV AUC: logistic 0.7737, depth-3 tree 0.6784, untuned forest 0.7466, tuned forest 0.7673. **Select logistic regression.** Use a scaler+logistic pipeline inside each CV fold. Out-of-fold threshold 0.50: precision 0.5753, recall 0.2485, F1 0.3471, 73 flagged. Threshold 0.35: precision 0.5130, recall 0.4675, F1 0.4892, 154 flagged. **Select 0.35 by higher F1 and recall.** Fit winner on full training data and evaluate once on test: precision 0.5714, recall 0.5714, ROC-AUC 0.7889, 49/198 flagged. Export 198 rows to `test_risk_scores.csv`. A real clinic should choose calling thresholds using evening staff capacity and empty-slot cost.

## Part 4 — Generative AI (22 marks)

### Task 4.1 — One validated Gemini call (5)
`04_genai.ipynb` includes the Gemini Flash JSON schema, CRAFT prompt, temperature 0, and Pydantic checks. It needs **your own private Gemini API key** and a networked execution. The N001 note explicitly says no reminder was received and the visit was forgotten; expected root cause is `forgot_or_no_reminder`. **No actual Gemini response is claimed in this document.**

### Task 4.2 — First ten notes and validation (7)
The notebook skips blank N004 without an API call and writes 10 rows × 8 columns, retaining raw JSON and invalid responses. Below is a **manual answer key based on the notes**, not `notes_analysed.csv` produced by Gemini:

| Note | Expected category | Evidence |
|---|---|---|
| N001 | forgot_or_no_reminder | Did not receive reminder; forgot |
| N002 | distance_or_transport | Long distance; no transport |
| N003 | cost_or_fee | Consultation fee too high |
| N004 | other | Blank note, skipped_blank, confidence 0 |
| N005 | illness_or_emergency | Fever and body ache |
| N006 | work_or_schedule | Urgent work meeting |
| N007 | forgot_or_no_reminder | Hinglish: forgot; no SMS |
| N008 | distance_or_transport | Bus strike and no auto |
| N009 | other | Could not contact patient; reason unknown |
| N010 | work_or_schedule | Factory shift change |

The manual answer key contains categories: reminders 2, distance 2, cost 1, illness 1, work 2, other 2. These are **not model-generated classifications**.

### Task 4.3 — Failure testing and prompt comparison (5)
The notebook tests Pydantic with confidence=1.7 (must fail `le=1`) and a missing `recommended_action` (must fail required field), catching both `ValidationError`s. It calls Gemini twice each for N007 and N009: V1 minimal prompt versus V2 CRAFT prompt, using the same JSON schema and temperature. Compare four actual responses, select the prompt that returns allowed categories and does not guess on ambiguous N009, and print the actual API call count (expected 12–14 depending on reuse). **These API comparisons have not been run.**

### Task 4.4 — Recommendation, crosstab and GitHub (5)
The notebook merges ten note IDs to cleaned appointments and prints `pd.crosstab(root_cause, reminder_sent)`. The assignment's reference says 5/10 notes have reminder_sent='No', and both N001/N007 are in that group; this can be verified from the local CSV independently. The **actual Gemini-derived crosstab** must wait for real responses. Use the README's four-line summary, recommendation and limitations, and upload one public repository without any API key.

**Provisional business recommendation:** Call patients with high predicted no-show risk the evening before the visit, prioritising long-lead bookings and checking reminder delivery. The overall no-show rate is 22.0% (218/990); 31+ day bookings show 60.5% (26/43) versus 16.2% (63/390) for 1–7 days. Logistic regression achieved training CV ROC-AUC 0.7737 and held-out ROC-AUC 0.7889; threshold 0.35 flags 49/198 test bookings with 57.1% recall. The manual review of ten notes suggests transport, reminders and work scheduling are actionable themes, **but these ten are not representative of all patients and are not Gemini API findings**. Start with a limited call pilot, track actual attendance and calls made, and recalibrate against capacity.

**Limitations (at least three):** (1) only ten illustrative notes, not clinic-wide evidence; (2) cleaning medians/quartiles used the full dataset before splitting; (3) random split may include the same patient in train and test; (4) chronological deployment differs from random testing; (5) observational associations do not establish causes; (6) threshold depends on call capacity.

## How to use this without Google Colab

Google Colab is **not mandatory**. Install Python and Jupyter (or VS Code with the Jupyter extension), unzip this project, open the notebooks in the project folder, install `pandas numpy scikit-learn requests google-genai pydantic`, and run cells from top to bottom. For SQL, use MySQL Workbench or SQLiteOnline. The provided `run_local.py` checks the locally reproducible outputs without an account. **Live weather and Gemini still require internet, and Gemini requires your own private API key.** A text-only answer does not satisfy the assignment's requirement to submit a public GitHub repository with notebooks, generated files and original data.


## Supplement: final manual review and integrated conclusion

See `MANUAL_NOTES_REPORT.md` for each of N001–N010, a reminder cross-tab and provenance. See the expanded `README.md` for the integrated evidence-backed recommendation. API-dependent observations are marked pending rather than simulated.
