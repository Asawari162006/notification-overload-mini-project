"""Live HTTP smoke demo. Requires the server; resets only simulator data."""
import json
from pathlib import Path
import httpx

BASE='http://127.0.0.1:8000'
def main():
 with httpx.Client(base_url=BASE,timeout=120) as c:
  def get(path):
   r=c.get(path);r.raise_for_status();return r.json()
  def post(path,payload=None):
   r=c.post(path,json=payload);r.raise_for_status();return r.json()
  status=get('/api/status'); assert status['model_status']=='trained',status.get('model_reason')
  audit=get('/api/audit');assert audit['raw_rows']==176195;assert audit['duplicate_participant_traces']=={'7':'6'}
  evaluation=get('/api/evaluation');assert set(evaluation['experiments'])=={'A','B'}
  prediction=post('/api/predict',{'participant':'smoke-new-user','source':'unseen.example','posted_at':1528232400});assert prediction['predicted_duration']>=0 and prediction['fallback_information']
  load=get('/api/load?participant=1');assert load['unusual_count']>0
  replay=get('/api/replay?participant=1&limit=3');assert len(replay['items'])==3
  before=audit['usable_samples'];seed=post('/api/simulator/seed');assert seed['delivered_items']==1
  done=post('/api/simulator/clock',{'time':330});assert done['delivered_items']==4 and done['alerts']==2
  repeat=post('/api/simulator/clock',{'time':330});assert repeat['alerts']==2
  assert get('/api/audit')['usable_samples']==before
  assert c.get('/').status_code==200
  result={'status':'passed','dataset_checksum':audit['sha256'],'usable_samples':before,'models':{k:v['selected'] for k,v in evaluation['experiments'].items()},'prediction':prediction,'real_unusual_posting_cutoffs':load['unusual_count'],'replay_items':len(replay['items']),'synthetic_policy_alerts':done['alerts'],'synthetic_delivered_items':done['delivered_items'],'real_data_unchanged':True}
  Path('artifacts/smoke.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__': main()
