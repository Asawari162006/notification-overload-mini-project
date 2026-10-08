"""Local API. Real research data is read-only; simulated policy queues are separate."""
import json,math,threading
from pathlib import Path
import numpy as np
import pandas as pd
from fastapi import FastAPI,HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel,Field,ConfigDict
from ml.data import ROOT
from backend.store import Store
from backend.model import ModelService

class Context(BaseModel):
    model_config=ConfigDict(extra='forbid',allow_inf_nan=False)
    participant:str=Field(min_length=1,max_length=40)
    source:str=Field(min_length=1,max_length=150)
    posted_at:float=Field(gt=0,lt=4102444800)
    priority:int|None=Field(default=None,ge=-2,le=2)
    ringer:int|None=Field(default=None,ge=0,le=2)
    idle:int|None=Field(default=None,ge=0,le=1)
    interactive:int|None=Field(default=None,ge=0,le=1)
    screen_state:int|None=Field(default=None,ge=0,le=4)
class Preferences(BaseModel):
    model_config=ConfigDict(extra='forbid')
    protected_sources:list[str]=Field(max_length=50)
    digest_interval_seconds:int=Field(ge=10,le=86400)
    maximum_delay_seconds:int=Field(ge=1,le=86400)
class Notification(BaseModel):
    model_config=ConfigDict(extra='forbid',allow_inf_nan=False)
    key:str=Field(min_length=1,max_length=150)
    source:str=Field(min_length=1,max_length=150)
    title:str=Field(min_length=1,max_length=300)
    posted_at:float=Field(ge=0,lt=4102444800)
    mode:str=Field(pattern='^(synthetic|historical)$')
class Clock(BaseModel):
    model_config=ConfigDict(allow_inf_nan=False)
    time:float=Field(ge=0,lt=4102444800)

def read_json(name):
    p=ROOT/'artifacts'/name
    return json.loads(p.read_text()) if p.exists() else None

def create_app(db_url=None,artifact_directory=None):
    app=FastAPI(title='Notification Overload Analysis and Removal Time Prediction',version='1.0.0')
    app.add_middleware(CORSMiddleware,allow_origins=['http://localhost:5173','http://127.0.0.1:5173'],allow_methods=['GET','POST','PUT'],allow_headers=['Content-Type'])
    store=Store(db_url); model=ModelService(artifact_directory); lock=threading.RLock()
    feature_path=ROOT/'data/processed/features.csv'
    feature_cache=pd.read_csv(feature_path).set_index('episode_id') if feature_path.exists() else None
    path=ROOT/'data/processed/lineage.csv'
    events=pd.read_csv(path,dtype={'participant':str}) if path.exists() else pd.DataFrame()
    if len(events):
        events=events.loc[events.reason!='duplicate_participant_trace'].copy()
        events.loc[events.reason!='usable','removed_at']=np.nan
    def history(event):
        if not len(events): return []
        return events[(events.participant==event['participant'])&(events.posted_at<event['posted_at'])].to_dict('records')
    def guarded(fn,*args):
        try:
            with lock: return fn(*args)
        except ValueError as e: raise HTTPException(422,str(e))
        except KeyError: raise HTTPException(404,'Item not found')
    @app.get('/api/status')
    def status(): return {'dataset':'verified real dataset' if len(events) else 'unavailable','audit':read_json('audit.json'),'model_status':model.status,'model_reason':model.reason,'model':model.meta,'evaluation':read_json('evaluation.json'),'synthetic_data_in_evaluation':False}
    @app.get('/api/audit')
    def audit(): return read_json('audit.json') or {'status':'unavailable'}
    @app.get('/api/evaluation')
    def evaluation(): return read_json('evaluation.json') or {'status':'untrained','experiments':{}}
    @app.get('/api/analysis')
    def analysis():
        if not len(events): return {'status':'unavailable','sources':[],'participants':[],'duration':[],'load':[]}
        clean=events[events.reason=='usable']; d=clean.duration_seconds
        bins=[0,1,10,60,300,3600,86400,float('inf')]; labels=['0–1s','1–10s','10–60s','1–5m','5–60m','1–24h','>24h']
        hist=pd.cut(d,bins=bins,labels=labels,include_lowest=True).value_counts(sort=False)
        load=events.assign(window=(events.posted_at//900)*900).groupby('window').size()
        sources=clean.groupby('source').agg(count=('episode_id','size'),median_seconds=('duration_seconds','median')).sort_values('count',ascending=False).head(15).reset_index().to_dict('records')
        users=clean.groupby('participant').agg(count=('episode_id','size'),median_seconds=('duration_seconds','median')).reset_index().to_dict('records')
        return {'status':'real dataset descriptive analysis; entire audited period, not held-out metrics','sources':sources,'participants':users,'duration':[{'range':str(k),'count':int(v)} for k,v in hist.items()],'load':[{'time':float(k),'count':int(v)} for k,v in load.items()]}
    @app.post('/api/predict')
    def predict(input:Context):
        data=input.model_dump(); data={k:(np.nan if v is None else v) for k,v in data.items()}
        try: return model.predict(data,history(data))
        except ValueError as e: raise HTTPException(503,str(e))
    @app.get('/api/replay')
    def replay(participant:str='1',offset:int=0,limit:int=50):
        if offset<0 or limit<1 or limit>200: raise HTTPException(422,'Invalid pagination')
        if not len(events): return {'items':[],'total':0}
        rows=events[events.participant==participant].sort_values(['posted_at','episode_id']); page=rows.iloc[offset:offset+limit]
        items=[]
        for row in page.to_dict('records'):
            ctx={k:row.get(k) for k in ['participant','source','posted_at','priority','ringer','idle','interactive','screen_state']}
            items.append({'episode_id':row['episode_id'],'participant':participant,'source':row['source'],'posted_at':row['posted_at'],'observed_duration_seconds':float(row['duration_seconds']) if row['reason']=='usable' else None,'episode_status':row['reason'],'prediction':model.predict(ctx,[] if feature_cache is not None else history(ctx),feature_cache.loc[[row['episode_id']]] if feature_cache is not None else None)})
        return {'items':items,'total':len(rows),'participant':participant,'history_mode':'real posting order; prediction only sees earlier outcomes'}
    @app.get('/api/load')
    def load(participant:str='1'):
        if not len(events) or model.model is None: return {'status':'unavailable','points':[]}
        from ml.features import FeatureState
        state=FeatureState(); points=[]; ref=model.meta['load']
        for row in events[events.participant==participant].sort_values(['posted_at','episode_id']).to_dict('records'):
            f=state.at(row); n=f['count_15m']; points.append({'time':row['posted_at'],'current':n,'reference':ref['reference'],'threshold':ref['threshold'],'unusual':n>ref['threshold']})
        # Consecutive representative points, plus all unusual points are accessible via API.
        return {'status':'real data; reference fitted on B training periods only','window':'previous 15 minutes strictly before posting','points':points,'reference':ref,'unusual_count':sum(p['unusual'] for p in points),'anomaly_accuracy':None}
    @app.get('/api/simulator')
    def simulator(): return store.snapshot()
    @app.post('/api/simulator/ingest')
    def ingest(item:Notification): return guarded(store.ingest,item.model_dump())
    @app.post('/api/simulator/clock')
    def clock(c:Clock): return guarded(store.advance,c.time)
    @app.post('/api/simulator/deliver/{key}')
    def deliver(key:str): return guarded(store.deliver,key)
    @app.post('/api/simulator/reset')
    def reset(): return guarded(store.reset)
    @app.post('/api/simulator/seed')
    def seed():
        with lock:
            store.reset(); store.preferences({'protected_sources':['demo.emergency'],'digest_interval_seconds':300,'maximum_delay_seconds':600})
            for i,(source,t) in enumerate([('demo.emergency',0),('demo.social',10),('demo.social',20),('demo.mail',30)]): store.ingest({'key':f'synthetic:{i}','source':source,'title':f'Synthetic demonstration {i+1}','posted_at':t,'mode':'synthetic'})
            return store.advance(30)
    @app.get('/api/preferences')
    def preferences(): return store.preferences()
    @app.put('/api/preferences')
    def save(p:Preferences): return guarded(store.preferences,p.model_dump())
    @app.get('/api/model-card')
    def card(): return {'status':model.status,'metadata':model.meta,'text':(ROOT/'MODEL_CARD.md').read_text() if (ROOT/'MODEL_CARD.md').exists() else 'Untrained. Removal is not reading; unusual load is not fatigue.'}
    if (ROOT/'frontend/dist').exists(): app.mount('/',StaticFiles(directory=ROOT/'frontend/dist',html=True),name='frontend')
    return app

app=create_app()
