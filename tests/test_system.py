import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal
from fastapi.testclient import TestClient
from ml.data import reconstruct,parse_sql,ROOT
from ml.features import build_features,inference_features,COLUMNS
from ml.splits import split_a,split_b
from ml.pipeline import metrics,candidate
from backend.model import ModelService
from backend.store import Store
from backend.app import create_app

def events():
 return pd.DataFrame([
  dict(participant='1',id=1,nid=1,source='a',posted_at=100,removed_at=300,priority=0,ringer=2,idle=0,interactive=1,screen_state=2,episode_id='1:1'),
  dict(participant='1',id=2,nid=2,source='b',posted_at=200,removed_at=210,priority=0,ringer=2,idle=0,interactive=1,screen_state=2,episode_id='1:2'),
  dict(participant='1',id=3,nid=3,source='a',posted_at=250,removed_at=270,priority=0,ringer=2,idle=0,interactive=1,screen_state=2,episode_id='1:3'),
  dict(participant='1',id=4,nid=4,source='c',posted_at=300,removed_at=300,priority=0,ringer=2,idle=0,interactive=1,screen_state=2,episode_id='1:4'),
  dict(participant='1',id=5,nid=5,source='a',posted_at=301,removed_at=400,priority=0,ringer=2,idle=0,interactive=1,screen_state=2,episode_id='1:5')])

def test_duration_and_conservative_identity():
 e=events(); e.loc[1,'removed_at']=0;e.loc[2,'removed_at']=249
 duplicate=e.iloc[[0]].copy();duplicate['id']=6
 ep,clean=reconstruct(pd.concat([e,duplicate],ignore_index=True))
 assert len(ep)==5 and len(clean)==3
 assert clean.loc[clean.id==1,'duration_seconds'].iloc[0]==200
 assert clean.loc[clean.id==4,'duration_seconds'].iloc[0]==0
 assert ep.loc[ep.id==1,'raw_ids'].iloc[0]=='1,6'
 assert set(ep.reason)=={'usable','unknown_removal','negative_duration'}

def test_conflicts_overlaps_and_missing():
 e=events();e.loc[1,['nid','source']]=[1,'a']
 conflict=e.iloc[[4]].copy();conflict['id']=6;conflict['removed_at']=500
 missing=e.iloc[[3]].copy();missing['id']=7;missing['posted_at']=np.nan
 ep,_=reconstruct(pd.concat([e,conflict,missing],ignore_index=True))
 assert ep.loc[ep.id==1,'reason'].iloc[0]=='overlapping_identity'
 assert ep.loc[ep.id==5,'reason'].iloc[0]=='conflicting_removals'
 assert ep.loc[ep.id==7,'reason'].iloc[0]=='invalid_posting'

def test_shared_features_cutoffs_and_parity():
 e=events();x=build_features(e)
 assert np.isnan(x.loc[1,'user_median']) # 100's outcome not available at 200
 assert x.loc[2,'user_median']==10
 assert x.loc[3,'user_median']==15 # 300 outcomes not yet observable
 assert x.loc[4,'user_median']==15 # values [10,20,200,0]
 assert x.loc[1,'count_5m']==1
 inferred=inference_features(e.iloc[4].to_dict(),e.iloc[:4].to_dict('records'))
 assert_frame_equal(inferred.reset_index(drop=True),x.iloc[[4]].reset_index(drop=True),check_dtype=False)
 changed=e.copy();changed.loc[4,'removed_at']=90000
 assert_frame_equal(build_features(changed).iloc[:4],x.iloc[:4])

def test_simultaneous_posting_is_not_prior_load():
 e=events();e.loc[1,'posted_at']=100
 x=build_features(e);assert x.loc[1,'count_5m']==0

def grouped_events():
 return pd.concat([events().assign(participant=str(u),episode_id=lambda d: str(u)+':'+d.id.astype(str)) for u in range(1,8)],ignore_index=True)

def test_participant_separation():
 e=grouped_events();dev,test,folds,_=split_a(e)
 assert set(e.loc[dev,'participant']).isdisjoint(e.loc[test,'participant'])
 for t,v in folds: assert set(e.loc[t,'participant']).isdisjoint(e.loc[v,'participant'])

def test_chronological_label_availability():
 e=grouped_events();dev,test,folds,meta=split_b(e)
 for i in dev:
  c=meta['boundaries'][str(e.loc[i,'participant'])]['final_fit_cutoff']
  assert e.loc[i,'removed_at']<c and e.loc[i,'posted_at']<c
 for t,v in folds:
  for i in t: assert e.loc[i,'removed_at']<meta['boundaries'][str(e.loc[i,'participant'])]['development_cutoff']
 assert set(dev).isdisjoint(test)

def test_preprocessing_training_only_and_unknown_category():
 e=events();x=build_features(e);model=candidate('ridge',COLUMNS,1).fit(x.iloc[:3],e.duration_seconds.iloc[:3] if 'duration_seconds' in e else np.array([200,10,20]))
 encoder=model.named_steps['preprocess'].named_transformers_['source'].named_steps['encode']
 assert 'c' not in encoder.categories_[0]
 assert np.isfinite(model.predict(x.iloc[[3]])).all()
 train_median=model.named_steps['preprocess'].named_transformers_['numeric'].named_steps['impute'].statistics_[0]
 assert train_median==0

def test_hand_metrics():
 m=metrics([0,10,100],[0,20,80],['a','a','b'])
 assert m['mae_seconds']==10
 assert m['median_absolute_error_seconds']==10
 assert m['rmse_seconds']==pytest.approx((500/3)**.5)
 assert m['participant_average_mae_seconds']==12.5

def test_missing_corrupt_artifact(tmp_path):
 s=ModelService(tmp_path);assert s.status=='unavailable'
 assert s.predict(events().iloc[0].to_dict(),[])['predicted_duration'] is None
 (tmp_path/'model.joblib').write_bytes(b'not a model');(tmp_path/'model_metadata.json').write_text('{}')
 assert ModelService(tmp_path).status=='invalid'

def item(key='x',source='social',t=10):return dict(key=key,source=source,title='Synthetic item',posted_at=t,mode='synthetic')

def test_restart_and_idempotence(tmp_path):
 url=f'sqlite:///{tmp_path / "queue.db"}';s=Store(url);s.ingest(item());s.ingest(item());s.advance(130)
 assert len(s.snapshot()['items'])==1
 s2=Store(url);assert s2.snapshot()['clock']==130
 assert s2.snapshot()['items'][0]['status']=='deadline'
 s2.advance(600);s2.deliver('x');assert s2.snapshot()['alerts']==1
 assert s2.snapshot()['items'][0]['delivered_at']==130

def test_protected_and_deadline_precedence(tmp_path):
 s=Store(f'sqlite:///{tmp_path / "q.db"}')
 s.preferences({'protected_sources':['emergency'],'digest_interval_seconds':100,'maximum_delay_seconds':90})
 s.ingest(item('p','emergency'));s.ingest(item('d'))
 assert next(r for r in s.snapshot()['items'] if r['key']=='p')['status']=='scheduled_protected'
 s.advance(10)
 assert next(r for r in s.snapshot()['items'] if r['key']=='p')['delivered_at']==10
 s.advance(100);r=next(x for x in s.snapshot()['items'] if x['key']=='d')
 assert r['status']=='deadline' and r['digest'] is None # deadline=100 ties digest

def test_digest_items_and_policy_snapshot(tmp_path):
 s=Store(f'sqlite:///{tmp_path / "q.db"}');s.preferences({'protected_sources':[],'digest_interval_seconds':100,'maximum_delay_seconds':500})
 s.ingest(item('a'));s.ingest(item('b',t=20));s.preferences({'protected_sources':['social'],'digest_interval_seconds':500,'maximum_delay_seconds':1})
 s.advance(100);rows=s.snapshot()['items'];assert len({r['digest'] for r in rows})==1
 assert s.snapshot()['alerts']==1 and all(r['status']=='digest' for r in rows)

def test_monotonic_and_future_manual(tmp_path):
 s=Store(f'sqlite:///{tmp_path / "q.db"}');s.ingest(item())
 with pytest.raises(ValueError):s.deliver('x')
 s.advance(20)
 with pytest.raises(ValueError):s.advance(10)
 with pytest.raises(ValueError):s.ingest(item('past',t=1))

def test_api_validation_and_synthetic_isolation(tmp_path):
 app=create_app(f'sqlite:///{tmp_path / "api.db"}',tmp_path);c=TestClient(app)
 assert c.post('/api/predict',json={'participant':'a','source':'b','posted_at':1,'priority':99}).status_code==422
 assert c.post('/api/predict',json={'participant':'a','source':'b','posted_at':1520000000000}).status_code==422
 assert c.post('/api/predict',json={'participant':'a','source':'b','posted_at':1,'removed_at':2}).status_code==422
 p=c.post('/api/predict',json={'participant':'new','source':'unseen','posted_at':100}).json();assert p['model_status']=='unavailable'
 before=c.get('/api/audit').json();c.post('/api/simulator/seed');assert c.get('/api/audit').json()==before
 assert c.get('/api/status').json()['synthetic_data_in_evaluation'] is False
 assert c.put('/api/preferences',json={'protected_sources':[],'digest_interval_seconds':0,'maximum_delay_seconds':0}).status_code==422
 assert c.post('/api/simulator/clock',json={'time':-1}).status_code==422

@pytest.mark.skipif(not (ROOT/'data/raw/ami2018_notifications.sql.zip').exists(),reason='Public archive not downloaded')
def test_real_timestamp_units():
 e,_=parse_sql(ROOT/'data/raw/ami2018_notifications.sql.zip')
 assert len(e)==176195 and e.participant.nunique()==14
 assert e.posted_at.min()>1_500_000_000 and e.posted_at.max()<1_600_000_000
 assert (e.removed_at==0).sum()==120380


def test_duplicate_participant_trace_detection():
 from ml.data import duplicate_traces
 e=events();copy=e.assign(participant='2');copy['episode_id']=e.episode_id
 assert duplicate_traces(pd.concat([e,copy],ignore_index=True))=={'2':'1'}

@pytest.mark.skipif(not (ROOT/'artifacts/model_metadata.json').exists(),reason='Real model not yet trained')
def test_real_cache_inference_parity_and_artifact():
 ep=pd.read_csv(ROOT/'data/processed/lineage.csv',dtype={'participant':str});ep=ep[ep.reason!='duplicate_participant_trace'].copy();ep.loc[ep.reason!='usable','removed_at']=np.nan
 f=pd.read_csv(ROOT/'data/processed/features.csv').set_index('episode_id')
 user=ep[ep.participant=='1'].sort_values(['posted_at','episode_id']);row=user.iloc[min(300,len(user)-1)].to_dict()
 shared=inference_features(row,user[user.posted_at<row['posted_at']].to_dict('records'))
 assert_frame_equal(shared.reset_index(drop=True),f.loc[[row['episode_id']],COLUMNS].reset_index(drop=True),check_dtype=False)
 service=ModelService();assert service.status=='trained'
 result=service.predict({'participant':'new','source':'unseen','posted_at':1528232400},[])
 assert result['predicted_duration']>=0 and len(result['fallback_information'])>=2

@pytest.mark.skipif(not (ROOT/'artifacts/splits.json').exists(),reason='Real manifests unavailable')
def test_real_frozen_manifests_and_label_cutoffs():
 import json
 e=pd.read_csv(ROOT/'data/processed/episodes.csv',dtype={'participant':str}).set_index('episode_id');sp=json.loads((ROOT/'artifacts/splits.json').read_text())
 assert '7' not in set(e.participant)
 a=sp['A'];assert set(e.loc[a['development'],'participant']).isdisjoint(e.loc[a['test'],'participant'])
 for fold in a['folds']:assert set(e.loc[fold['train'],'participant']).isdisjoint(e.loc[fold['validation'],'participant'])
 b=sp['B']
 for user,g in e.loc[b['development']].groupby('participant'):
  cutoff=b['design']['boundaries'][user]['final_fit_cutoff'];assert (g.removed_at<cutoff).all() and (g.posted_at<cutoff).all()
 assert set(b['development']).isdisjoint(b['test'])


def test_simultaneous_posting_full_feature_parity():
 e=events();e.loc[2,'posted_at']=200
 batch=build_features(e)
 for index,row in e.iterrows():
  history=e[e.posted_at<row.posted_at].to_dict('records')
  inferred=inference_features(row.to_dict(),history)
  assert_frame_equal(inferred.reset_index(drop=True),batch.iloc[[index]].reset_index(drop=True),check_dtype=False)
