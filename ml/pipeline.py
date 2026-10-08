"""Reproducible audit/features/splits/train/evaluate CLI. Real data only."""
import argparse, hashlib, json, platform, sys, runpy
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import sklearn
from threadpoolctl import threadpool_limits
from sklearn.compose import ColumnTransformer, TransformedTargetRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, median_absolute_error, mean_squared_error, r2_score
from ml.data import ROOT, audit, download
from ml.features import build_features, META, LOAD, SOURCE, PERSONAL, COLUMNS
from ml.splits import split_a, split_b

LIMITATIONS=['Removal does not prove reading, attention or importance.','Complete observed unambiguous episodes are a selected population.','14 participant IDs, 13 distinct recorded traces; notifications are not independent people.','Android tags, observation endpoints and local timezones are absent.','Recorded posting identity cannot establish first lifecycle posting.','Earlier history updates online as outcomes become known; cold-start performance differs.','Unusual load is not fatigue; simulator policies are not evidence of behavioural improvement.']

def metrics(actual,predicted,users):
    y=np.asarray(actual); p=np.maximum(0,np.asarray(predicted)); err=np.abs(y-p)
    per=pd.DataFrame({'user':np.asarray(users).astype(str),'error':err}).groupby('user').error.mean()
    return {'mae_seconds':float(mean_absolute_error(y,p)),'median_absolute_error_seconds':float(median_absolute_error(y,p)),'rmse_seconds':float(np.sqrt(mean_squared_error(y,p))),'r2':float(r2_score(y,p)) if len(y)>1 else None,'participant_average_mae_seconds':float(per.mean()),'per_participant_mae_seconds':per.to_dict(),'samples':len(y),'participants':len(per)}

from ml.models import Baseline

def candidate(name,columns,parameter=1):
    if name in ['global_median','historical_median']: return Baseline(name=='historical_median')
    numeric=[c for c in columns if c!='source']
    pre=ColumnTransformer([('numeric',Pipeline([('impute',SimpleImputer(strategy='median',add_indicator=True,keep_empty_features=True)),('scale',StandardScaler())]),numeric),('source',Pipeline([('impute',SimpleImputer(strategy='most_frequent')),('encode',OneHotEncoder(handle_unknown='ignore',sparse_output=False))]),['source'])],remainder='drop')
    models={'ridge':Ridge(alpha=parameter),'random_forest':RandomForestRegressor(n_estimators=60,max_depth=12,min_samples_leaf=parameter,n_jobs=2,random_state=42),'gradient_boosting':HistGradientBoostingRegressor(max_iter=100,max_leaf_nodes=15,l2_regularization=parameter,random_state=42)}
    return Pipeline([('preprocess',pre),('regressor',TransformedTargetRegressor(regressor=models[name],func=np.log1p,inverse_func=np.expm1))])

PARAMS={'global_median':[1],'historical_median':[1],'ridge':[1,10],'random_forest':[5,20],'gradient_boosting':[1,10]}

def features():
    ep=pd.read_csv(ROOT/'data/processed/lineage.csv',dtype={'participant':str})
    ep=ep.loc[ep.reason!='duplicate_participant_trace'].copy()
    ep.loc[ep.reason!='usable','removed_at']=np.nan
    f=build_features(ep)
    f['episode_id']=ep.episode_id; f.to_csv(ROOT/'data/processed/features.csv',index=False)
    return ep.loc[ep.reason=='usable'].reset_index(drop=True), f

def load_data():
    ep=pd.read_csv(ROOT/'data/processed/episodes.csv',dtype={'participant':str}).reset_index(drop=True)
    f=pd.read_csv(ROOT/'data/processed/features.csv').set_index('episode_id').loc[ep.episode_id,COLUMNS].reset_index(drop=True)
    return ep,f

def manifest():
    e,_=load_data(); result={}
    for name,fn in [('A',split_a),('B',split_b)]:
        dev,test,folds,meta=fn(e)
        result[name]={'development':e.loc[dev,'episode_id'].tolist(),'test':e.loc[test,'episode_id'].tolist(),'folds':[{'train':e.loc[t,'episode_id'].tolist(),'validation':e.loc[v,'episode_id'].tolist()} for t,v in folds],'design':meta}
    (ROOT/'artifacts/splits.json').write_text(json.dumps(result,indent=2)); return result

def index_ids(e,ids): return e.index[e.episode_id.isin(ids)].to_numpy()

def diagnostics(e,X,train,test,pred):
    y=e.loc[test,'duration_seconds'].to_numpy(); err=np.abs(y-pred)
    cuts=np.unique(e.loc[train,'duration_seconds'].quantile([.5,.9,.99]).to_numpy()).tolist()
    ranges=pd.cut(y,[-np.inf]+cuts+[np.inf]).astype(str)
    freq=X.loc[train,'source'].value_counts(); s=X.loc[test,'source'].map(freq).fillna(0)
    masks={'unseen_source':s==0,'rare_source_training_count_1_to_20':(s>0)&(s<=20),'frequent_source':s>20,'sparse_history':X.loc[test,'user_history_count']<5,'missing_context':X.loc[test,META[1:]].isna().any(axis=1),'cold_start_user':X.loc[test,'user_history_count']==0,'high_load':X.loc[test,'count_15m']>float(X.loc[train,'count_15m'].quantile(.95))}
    result={'training_duration_boundaries_seconds':cuts,'duration_ranges':{},'subgroups':{}}
    for label in sorted(set(ranges)):
        m=ranges==label; result['duration_ranges'][label]={'n':int(m.sum()),'mae_seconds':float(err[m].mean())}
    for label,m in masks.items():
        m=np.asarray(m); result['subgroups'][label]={'n':int(m.sum()),'mae_seconds':float(err[m].mean()) if m.any() else None}
    return result

def plots(e,test,pred,name):
    import matplotlib; matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    y=e.loc[test,'duration_seconds'].to_numpy()
    fig,axes=plt.subplots(1,2,figsize=(10,4)); axes[0].scatter(y,pred,s=4,alpha=.3); axes[0].set(xscale='symlog',yscale='symlog',xlabel='Observed seconds',ylabel='Predicted seconds',title='Prediction versus observed removal')
    axes[1].scatter(pred,y-pred,s=4,alpha=.3); axes[1].set(xscale='symlog',yscale='symlog',xlabel='Predicted seconds',ylabel='Observed minus predicted seconds',title='Residuals')
    fig.tight_layout(); fig.savefig(ROOT/f'artifacts/{name}_diagnostics.png',dpi=140); plt.close(fig)

def train():
    e,X=load_data(); y=e.duration_seconds; splits=json.loads((ROOT/'artifacts/splits.json').read_text()); audit_info=json.loads((ROOT/'artifacts/audit.json').read_text())
    result={'selection_objective':'development participant-average MAE in original seconds','target':'recorded removal minus recorded posting, Unix seconds','search':PARAMS,'target_transform':'log1p for Ridge, Random Forest, gradient boosting; inverse transformed, clamp negative to zero','history_policy':'All models use identical online updates. Only same-participant prior postings and strictly earlier usable removals enter dynamic features. A test users start cold; B history updates during replay. Frozen model parameters never update on test.','experiments':{},'limitations':LIMITATIONS}
    deploy=None
    for exp,sp in splits.items():
        dev=index_ids(e,sp['development']); test=index_ids(e,sp['test']); folds=[(index_ids(e,f['train']),index_ids(e,f['validation'])) for f in sp['folds']]
        scores=[]
        for name,parameters in PARAMS.items():
            for param in parameters:
                fold_metrics=[]
                for t,v in folds:
                    model=candidate(name,COLUMNS,param).fit(X.loc[t],y.loc[t]); pred=np.maximum(0,model.predict(X.loc[v])); fold_metrics.append(metrics(y.loc[v],pred,e.loc[v,'participant']))
                scores.append({'model':name,'parameter':param,'development_participant_mae':float(np.mean([v for m in fold_metrics for v in m['per_participant_mae_seconds'].values()])),'folds':fold_metrics})
                print(exp,name,param,scores[-1]['development_participant_mae'],flush=True)
        selected=min(scores,key=lambda z:z['development_participant_mae']); comparisons=[]; winner=None; winner_pred=None
        for name in PARAMS:
            best=min([s for s in scores if s['model']==name],key=lambda z:z['development_participant_mae'])
            model=candidate(name,COLUMNS,best['parameter']).fit(X.loc[dev],y.loc[dev]); pred=np.maximum(0,model.predict(X.loc[test])); comparisons.append({'model':name,'parameter':best['parameter'],'development_participant_mae':best['development_participant_mae'],'held_out':metrics(y.loc[test],pred,e.loc[test,'participant'])})
            if name==selected['model']: winner=model; winner_pred=pred
        # Ablation uses the fixed gradient booster, identical manifests, no test-based choices.
        ablations=[]
        for label,cols in [('A metadata',META),('B recent load',META+LOAD),('C source history',META+LOAD+SOURCE),('D personal history',COLUMNS)]:
            vals=[]
            for t,v in folds:
                model=candidate('gradient_boosting',cols,1).fit(X.loc[t],y.loc[t]); vals.append(metrics(y.loc[v],model.predict(X.loc[v]),e.loc[v,'participant'])['participant_average_mae_seconds'])
            ablations.append({'features':label,'development_participant_mae':float(np.mean(vals))})
        sample=np.linspace(0,len(test)-1,min(500,len(test)),dtype=int)
        result['experiments'][exp]={'design':sp['design'],'selected':selected['model'],'selected_parameter':selected['parameter'],'development_search':scores,'comparisons':comparisons,'ablations':ablations,'ablation_aggregation':'Mean of fold participant-average MAEs, fixed gradient booster; ablation scores are not used for model selection.','diagnostics':diagnostics(e,X,dev,test,winner_pred),'plot_sample':[{'actual':float(y.loc[test[i]]),'predicted':float(winner_pred[i])} for i in sample],'train_samples':len(dev),'test_samples':len(test),'test_participants':int(e.loc[test,'participant'].nunique())}
        pd.DataFrame({'episode_id':e.loc[test,'episode_id'].to_numpy(),'participant':e.loc[test,'participant'].to_numpy(),'actual':y.loc[test].to_numpy(),'predicted':winner_pred}).to_csv(ROOT/f'artifacts/{exp}_predictions.csv',index=False)
        plots(e,test,winner_pred,exp)
        if exp=='B':
            deploy=winner; deploy_indices=dev
    (ROOT/'artifacts/evaluation.json').write_text(json.dumps(result,indent=2,allow_nan=False))
    # Deploy the B final-fit model, preserving its test holdout. No all-data refit.
    version='mini-project-v1-B'; artifact_path=ROOT/'artifacts/model.joblib'
    joblib.dump(deploy,artifact_path)
    threshold=float(X.loc[deploy_indices,'count_15m'].quantile(.95)); ref=float(X.loc[deploy_indices,'count_15m'].mean())
    meta={'version':version,'model':result['experiments']['B']['selected'],'status':'trained','feature_schema':COLUMNS,'target':result['target'],'source':audit_info['source'],'source_sha256':audit_info['sha256'],'split':'B','split_sha256':hashlib.sha256((ROOT/'artifacts/splits.json').read_bytes()).hexdigest(),'artifact_sha256':hashlib.sha256(artifact_path.read_bytes()).hexdigest(),'dependencies':{'python':platform.python_version(),'scikit-learn':sklearn.__version__,'numpy':np.__version__,'pandas':pd.__version__,'joblib':joblib.__version__},'metrics':next(c['held_out'] for c in result['experiments']['B']['comparisons'] if c['model']==result['experiments']['B']['selected']),'load':{'window_seconds':900,'reference':ref,'threshold':threshold,'definition':'95th percentile of preceding 15-minute canonical posting counts at training posting cutoffs, including unknown-removal postings; strict threshold exceedance'},'known_sources':sorted(X.loc[deploy_indices,'source'].unique().tolist()),'limitations':LIMITATIONS}
    (ROOT/'artifacts/model_metadata.json').write_text(json.dumps(meta,indent=2))
    (ROOT/'EVALUATION_REPORT.md').write_text('# Actual evaluation\n\nFrozen manifests: artifacts/splits.json. Selection uses development participant-average MAE; test never selects the winner. Log target is inverse transformed; no invented accuracy percentage.\n\n'+json.dumps(result,indent=2)+'\n\nNo confidence percentage is estimated. Thirteen distinct traces among fourteen IDs limit generalization; participant-level errors describe variation, not independent-person certainty. Dynamic source histories are within participant. Static historical baseline uses training source/global medians only as fallback. Ablations compare fixed gradient boosting on development splits; differences describe predictive association, not causality. Valid long episodes remain and can dominate RMSE. No anomaly labels exist; no anomaly accuracy is reported.\n')
    (ROOT/'MODEL_CARD.md').write_text('# Model card\n\nIntended use: educational recorded removal-duration regression and historical replay. Not a measure of attention, importance, reading or fatigue; no phone control.\n\n'+json.dumps(meta,indent=2)+'\n\nExperiment A reserves participants with grouped development CV. Experiment B uses per-participant 60/80% posting-time boundaries, training labels observed before cutoff, and online outcome-history updates. Deployed artifact is the B development-fit model; B final test remains held out. Optional classification deferred because follow-up validity is unknown. Reserved future work: what-if explorer, input-quality guard dashboard, experiment cards and model-disagreement interface.\n')
    runpy.run_path(str(ROOT/'scripts/write_evaluation_report.py'))
    return result

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('command',choices=['download','audit','reconstruct','features','splits','train','evaluate','all']); a=parser.parse_args()
    if a.command in ['download','all']: download()
    if a.command in ['audit','reconstruct','all']: print(json.dumps(audit(),indent=2))
    if a.command in ['features','all']: features()
    if a.command in ['splits','all']: manifest()
    if a.command in ['train','all']:
        with threadpool_limits(limits=2): train()
    if a.command=='evaluate':
        path=ROOT/'artifacts/evaluation.json'
        if not path.exists(): raise SystemExit('No evaluated models; run train first')
        print(path.read_text())

if __name__=='__main__': main()
