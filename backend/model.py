"""Trusted local artifact loading with explicit missing/corrupt states."""
import hashlib,json
from pathlib import Path
import joblib
import numpy as np
import sklearn
from ml.data import ROOT
from ml.features import COLUMNS,inference_features

class ModelService:
    def __init__(self,directory=None):
        self.directory=Path(directory or ROOT/'artifacts'); self.model=None; self.meta={}; self.status='unavailable'; self.reason='No trained local artifact'
        try:
            p=self.directory/'model.joblib'; m=self.directory/'model_metadata.json'
            if not p.exists() or not m.exists(): return
            meta=json.loads(m.read_text())
            if meta['feature_schema']!=COLUMNS: raise ValueError('Feature schema mismatch')
            if meta['dependencies']['scikit-learn']!=sklearn.__version__: raise ValueError('scikit-learn version mismatch')
            if hashlib.sha256(p.read_bytes()).hexdigest()!=meta['artifact_sha256']: raise ValueError('Artifact checksum mismatch')
            self.model=joblib.load(p); self.meta=meta; self.status='trained'; self.reason=None
        except Exception as exc:
            self.model=None; self.status='invalid'; self.reason=str(exc)
    def predict(self,event,history,features=None):
        if self.model is None: return {'predicted_duration':None,'units':'seconds','model_version':None,'model_status':self.status,'fallback_information':[self.reason]}
        x=features if features is not None else inference_features(event,history); raw=float(self.model.predict(x)[0]); notes=[]
        if event['source'] not in self.meta['known_sources']: notes.append('Unseen source: unknown-category encoding or baseline global fallback')
        if x.user_history_count.iloc[0]==0: notes.append('No earlier observed user outcomes: training imputation/global fallback')
        missing=[k for k in ['priority','ringer','idle','interactive','screen_state'] if event.get(k) is None or (isinstance(event.get(k),float) and np.isnan(event.get(k)))]
        if missing: notes.append('Missing context imputed: '+', '.join(missing))
        if raw<0: notes.append('Negative raw prediction clamped to zero')
        if not np.isfinite(raw): raise ValueError('Non-finite prediction')
        load=self.meta['load']; count=int(x.count_15m.iloc[0])
        return {'predicted_duration':max(0,raw),'units':'seconds','model_version':self.meta['version'],'model_status':'trained','fallback_information':notes,'load':{'current':count,**load,'unusual':count>load['threshold']}}
