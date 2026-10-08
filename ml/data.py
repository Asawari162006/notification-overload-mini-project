"""Read values, never execute the downloaded SQL. Conservative episode reconstruction."""
import csv
import hashlib
import json
import re
import urllib.request
import zipfile
from datetime import date
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE = 'https://github.com/komis1/ami2018-notifications'
CITATION = 'Komninos, A., Frengkou, E., & Garofalakis, J. (2018). Predicting User Responsiveness to Smartphone Notifications for Edge Computing. AmI-18, Springer, Larnaca, Cyprus.'

def download():
    raw = ROOT / 'data/raw'
    raw.mkdir(parents=True, exist_ok=True)
    for name in ['ami2018_notifications.sql.zip', 'README.md', 'LICENSE']:
        target = raw / name
        if not target.exists():
            urllib.request.urlretrieve(f'https://raw.githubusercontent.com/komis1/ami2018-notifications/master/{name}', target)

def parse_sql(path):
    with zipfile.ZipFile(path) as archive:
        members = [x for x in archive.infolist() if x.filename.endswith('.sql')]
        if len(members) != 1 or members[0].file_size > 100_000_000:
            raise ValueError('Expected one SQL file smaller than 100 MB')
        sql = archive.read(members[0]).decode('utf8')
    rows = []
    for match in re.finditer(r'INSERT INTO `elton_notifications`\s*\((.*?)\) VALUES\s*(.*?);', sql, re.S):
        cols = re.findall(r'`([^`]+)`', match[1])
        for line in match[2].splitlines():
            line = line.strip().rstrip(',;')
            if not line.startswith('('):
                continue
            vals = next(csv.reader([line[1:-1]], quotechar="'", skipinitialspace=True, escapechar='\\'))
            if len(vals) != len(cols):
                raise ValueError('SQL value count mismatch')
            rows.append(dict(zip(cols, vals)))
    if not rows:
        raise ValueError('No supported INSERT statements found')
    frame = pd.DataFrame(rows).rename(columns={'user_id':'participant','packagename':'source','timeposted':'posted_at','timeremoved':'removed_at','ringermode':'ringer'})
    for col in frame.columns.difference(['participant','source','vibrationpattern']):
        frame[col] = pd.to_numeric(frame[col], errors='coerce')
    frame['participant'] = frame.participant.astype(str)
    return frame, sql[:sql.index('INSERT INTO')]

def reconstruct(frame):
    """Only exact posting identity can be deduplicated; absent Android tags prevent full lifecycle reconstruction."""
    keys = ['participant','source','nid','posted_at']
    ordered=frame.sort_values('id').copy()
    ordered['_positive_removal']=ordered.removed_at.where(ordered.removed_at>0)
    ordered['_raw_id']=ordered.id.astype(int).astype(str)
    grouped=ordered.groupby(keys,dropna=False,sort=False)
    ep=ordered.drop_duplicates(keys).set_index(keys)
    stats=grouped.agg(removal_count=('_positive_removal','nunique'),removal=('_positive_removal','min'),raw_ids=('_raw_id',','.join))
    ep=ep.drop(columns=['removed_at','_positive_removal','_raw_id']).join(stats).reset_index()
    ep['removed_at']=ep.removal.where(ep.removal_count==1)
    ep['episode_id']=ep.participant.astype(str)+':'+ep.id.astype(int).astype(str)
    ep['reason']='candidate'
    ep.loc[ep.removal_count==0,'reason']='unknown_removal'
    ep.loc[ep.removal_count>1,'reason']='conflicting_removals'
    ep.loc[(ep.removal_count==1)&(ep.removed_at<ep.posted_at),'reason']='negative_duration'
    ep.loc[~np.isfinite(ep.posted_at)|(ep.posted_at<=0),'reason']='invalid_posting'
    ep=ep.sort_values(['posted_at','episode_id']).reset_index(drop=True)
    next_post=ep.groupby(['participant','source','nid'],dropna=False).posted_at.shift(-1)
    ep.loc[(ep.reason=='candidate')&(next_post<ep.removed_at),'reason']='overlapping_identity'
    ep=ep.drop(columns=['removal_count','removal'])
    ep['duration_seconds'] = ep.removed_at - ep.posted_at
    ep.loc[ep.reason == 'candidate','reason'] = 'usable'
    return ep, ep.loc[ep.reason=='usable'].copy()

def duplicate_traces(frame):
    seen={}; duplicates={}
    for participant,g in frame.groupby('participant',sort=True):
        trace=g.drop(columns='participant').sort_values('id').reset_index(drop=True)
        fingerprint=hashlib.sha256(pd.util.hash_pandas_object(trace,index=False).values.tobytes()).hexdigest()
        if fingerprint in seen: duplicates[str(participant)]=seen[fingerprint]
        else: seen[fingerprint]=str(participant)
    return duplicates

def audit():
    path = ROOT/'data/raw/ami2018_notifications.sql.zip'
    frame, schema = parse_sql(path)
    ep, clean = reconstruct(frame)
    duplicate_participants=duplicate_traces(frame)
    ep.loc[ep.participant.isin(duplicate_participants),'reason']='duplicate_participant_trace'
    clean=ep.loc[ep.reason=='usable'].copy()
    out = ROOT/'data/processed'; out.mkdir(parents=True, exist_ok=True)
    frame.to_csv(out/'records.csv', index=False)
    ep.to_csv(out/'lineage.csv', index=False)
    clean.to_csv(out/'episodes.csv', index=False)
    endpoints = frame.groupby('participant').agg(first_post=('posted_at','min'),last_post=('posted_at','max'),last_recorded_removal=('removed_at','max')).reset_index()
    summary = dict(source=SOURCE,retrieval_date=str(date.today()),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),citation=CITATION,usage_terms='Repository GPL-3.0; README permits use for any purpose and requests academic citation. Preserve upstream license; no public redistribution performed.',raw_rows=len(frame),participants=frame.participant.nunique(),distinct_participant_traces=frame.participant.nunique()-len(duplicate_participants),duplicate_participant_traces=duplicate_participants,timestamp_units='Unix seconds (10-digit values, 2018 range); SQL session +00:00. Participant local timezones unknown; calendar features omitted.',schema=schema,types={c:str(t) for c,t in frame.dtypes.items()},missingness={c:int(frame[c].isna().sum()) for c in frame},zero_removal_records=int((frame.removed_at==0).sum()),invalid_order_records=int(((frame.removed_at>0)&(frame.removed_at<frame.posted_at)).sum()),duplicate_serial_ids=int(frame.duplicated(['participant','id']).sum()),duplicate_posting_identity=int(frame.duplicated(['participant','source','nid','posted_at']).sum()),exclusions={str(k):int(v) for k,v in ep.reason.value_counts().items()},usable_samples=len(clean),zero_durations=int((clean.duration_seconds==0).sum()),duration_quantiles={str(k):float(v) for k,v in clean.duration_seconds.quantile([0,.25,.5,.75,.95,.99,1]).items()},endpoints=endpoints.to_dict('records'),removal_reasons='Not available',followup='Observation endpoints are last logged events, not verified monitoring end times. Missing removal is unknown, not established censoring.')
    (ROOT/'artifacts/audit.json').write_text(json.dumps(summary,indent=2))
    (ROOT/'DATA_FEASIBILITY.md').write_text('# Dataset feasibility\n\n'+json.dumps(summary,indent=2)+'\n\n## Decision before training\nObserved-duration regression is supportable only for conservative, unambiguous recorded posting episodes. Same participant/package/nid/posting-second rows are consolidated, taking earliest serial metadata. Conflicting removals and identities with another posting strictly before removal are excluded. Android notification tags and first lifecycle posting are absent: identities cannot be fully reconstructed. Zero-removal rows at earlier posting times cannot safely be attached to later removals. This target is recorded posting-to-removal, not a proven complete notification lifetime. All exclusions have raw serial lineage. Participant 7 is an exact copy of participant 6 after removing participant ID; trace 7 is preserved but excluded from supervised evaluation and history to prevent leakage. The 14 IDs represent only 13 distinct recorded traces; identity of people cannot be verified. Valid extremes and zero durations are retained.\n\nThe included sample is selected on observed removal and unambiguous identity, and may overrepresent short durations. Evaluation does not apply to all phone notifications. No defensible censoring endpoints or removal reasons exist; survival analysis and optional horizon classification are deferred. Timestamp magnitudes demonstrate seconds despite Android API millisecond output. No local-calendar assumptions are made.\n')
    (ROOT/'DATA_DICTIONARY.md').write_text('# Data dictionary\n\n'+schema+'\n\nINSERT records populate 19 fields; six declared location fields are omitted and not predictors. user_id is participant; id is device logging serial unique with user_id; nid is reusable Android notification ID, not globally unique. packageName is source. timePosted/timeRemoved are stored Unix seconds, zero removal means unknown. priority is programmed priority, not importance. ringerMode, idle, interactive and screen_state are device context. Sound/LED/vibration/defaults/flags are recorded programming metadata. No removal reason, Android tag, monitoring endpoint or participant timezone is supplied. Derived fields: episode_id, raw_ids, reason, duration_seconds. See lineage.csv for every record group.\n')
    return summary
