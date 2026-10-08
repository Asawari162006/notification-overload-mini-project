"""Frozen deterministic manifests; label availability is distinct from posting time."""
import numpy as np
from sklearn.model_selection import GroupKFold

def split_a(events):
    users=sorted(events.participant.astype(str).unique(),key=lambda x:int(x) if x.isdigit() else x)
    rng=np.random.default_rng(42); shuffled=np.array(users); rng.shuffle(shuffled)
    test_users=shuffled[:max(1,round(len(users)*.2))].tolist()
    test=events.index[events.participant.astype(str).isin(test_users)].to_numpy()
    dev=events.index[~events.participant.astype(str).isin(test_users)].to_numpy()
    folds=[]
    for a,b in GroupKFold(n_splits=min(3,len(users)-len(test_users))).split(dev,groups=events.loc[dev,'participant']):
        folds.append((dev[a],dev[b]))
    return dev,test,folds,{'test_participants':test_users,'seed':42}

def split_b(events):
    # Per-participant time boundaries allow all observed users to appear in B.
    train=[]; val=[]; test=[]; boundaries={}
    for user,g in events.groupby('participant'):
        c1,c2=g.posted_at.quantile([.6,.8]).to_numpy()
        train.extend(g.index[(g.posted_at<c1)&(g.removed_at<c1)])
        val.extend(g.index[(g.posted_at>=c1)&(g.posted_at<c2)])
        test.extend(g.index[g.posted_at>=c2])
        boundaries[str(user)]={'development_cutoff':float(c1),'final_fit_cutoff':float(c2)}
    final=[]
    for user,g in events.groupby('participant'):
        c=boundaries[str(user)]['final_fit_cutoff']
        final.extend(g.index[(g.posted_at<c)&(g.removed_at<c)])
    return np.array(final),np.array(test),[(np.array(train),np.array(val))],{'boundaries':boundaries,'labels':'Only removals strictly before each fit cutoff; online historical outcomes update strictly before posting for every model.'}
