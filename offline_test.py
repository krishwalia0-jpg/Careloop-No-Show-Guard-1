"""Offline fixtures only. No external API calls or measured temperatures."""
import json
from pathlib import Path
import pandas as pd
from pydantic import BaseModel, Field, ValidationError, field_validator
ROOT=Path(__file__).resolve().parent
ALLOWED={'forgot_or_no_reminder','distance_or_transport','cost_or_fee','illness_or_emergency','work_or_schedule','other'}
class FollowupInsight(BaseModel):
    root_cause:str=Field(min_length=3)
    confidence:float=Field(ge=0,le=1)
    summary:str=Field(min_length=5)
    recommended_action:str=Field(min_length=5)
    @field_validator('root_cause')
    @classmethod
    def allowed(cls,v):
        if v not in ALLOWED: raise ValueError('Unknown category')
        return v
    @field_validator('summary')
    @classmethod
    def length(cls,v):
        if len(v.split())>25: raise ValueError('Too many words')
        return v
notes=pd.read_csv(ROOT/'notes_manual_review.csv').fillna('')
for i,r in notes.iterrows():
    if r.note_id=='N004':
        notes.loc[i,['confidence','summary','recommended_action','validation_status']]=[0.0,'No note recorded','Re-call patient','skipped_blank']; continue
    payload={k:r[k] for k in ['root_cause','summary','recommended_action']}
    payload['confidence']=0.5 if r.note_id=='N009' else 0.95
    FollowupInsight(**payload)
    notes.loc[i,['confidence','validation_status','raw_response']]=[payload['confidence'],'valid',json.dumps(payload)]
notes.to_csv(ROOT/'notes_analysed.csv',index=False)
clinics=pd.read_csv(ROOT/'data/clinics.csv'); clinics['temp_c']=[19.2,19.5,18.1,15.4,15.1,25.6,16.8,16.2]; clinics.to_csv(ROOT/'clinics_enriched_mock.csv',index=False)
lines=['# Offline test results — simulated, not API evidence','', 'Task 1.5: Eight illustrative temperature fixtures in clinics_enriched_mock.csv. Actual temperatures remain unknown; canonical weather file retains NULLs.','', 'Task 4.1: N001 fixture: '+notes.iloc[0].raw_response,'','Task 4.2: Nine fixtures passed Pydantic; N004 skipped. Confidence values are arbitrary test inputs, not model estimates.','', 'Task 4.3: Deliberate validation failures:']
good=json.loads(notes.iloc[0].raw_response)
for bad in [dict(good,confidence=1.7),{k:v for k,v in good.items() if k!='recommended_action'}]:
    try: FollowupInsight(**bad)
    except ValidationError as e: lines.append(str(e))
lines += ['', 'Prompt comparison fixtures (not actual prompt performance):','', '|Note|Prompt|Category|Valid|','|---|---|---|---|']
for nid,v1 in [('N007','forgot'),('N009','unreachable')]:
    base=json.loads(notes.loc[notes.note_id==nid,'raw_response'].iloc[0])
    for variant,category in [('V1',v1),('V2',base['root_cause'])]:
        try: FollowupInsight(**dict(base,root_cause=category)); valid=True
        except ValidationError: valid=False
        lines.append(f'|{nid}|{variant}|{category}|{valid}|')
merged=notes.merge(pd.read_csv(ROOT/'appointments_clean.csv'),on='appointment_id',validate='one_to_one')
lines += ['', 'V2 fixtures demonstrate allowed categories; no empirical prompt comparison is possible offline. Actual API calls: 0.', '', 'Task 4.4: Manual labels joined to actual reminder records:', '```',pd.crosstab(merged.root_cause,merged.reminder_sent).to_string(),'```',f'No reminder: {(merged.reminder_sent=="No").sum()} of 10.']
(ROOT/'OFFLINE_TEST_REPORT.md').write_text('\n'.join(lines)+'\n')
