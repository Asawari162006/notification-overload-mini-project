"""Posting-cutoff features shared by batch training, replay and API inference."""
from collections import defaultdict, deque, Counter
import heapq
import numpy as np
import pandas as pd

META = ['source','priority','ringer','idle','interactive','screen_state']
LOAD = ['count_5m','count_15m','count_30m','distinct_sources','since_previous','load_reference','load_deviation','missing_load_history']
SOURCE = ['source_median','source_history_count']
PERSONAL = ['user_median','user_history_count','missing_outcome_history']
COLUMNS = META + LOAD + SOURCE + PERSONAL

class Median:
    def __init__(self): self.low=[]; self.high=[]
    def add(self,x):
        heapq.heappush(self.low,-float(x))
        heapq.heappush(self.high,-heapq.heappop(self.low))
        if len(self.high)>len(self.low): heapq.heappush(self.low,-heapq.heappop(self.high))
    def value(self):
        if not self.low: return np.nan
        return -self.low[0] if len(self.low)>len(self.high) else (self.high[0]-self.low[0])/2
    def __len__(self): return len(self.low)+len(self.high)

class FeatureState:
    def __init__(self):
        self.windows={m:deque() for m in (5,15,30)}; self.source_counts=Counter(); self.current_posts=[]; self.pending=[]; self.user=Median(); self.sources=defaultdict(Median)
        self.last=None; self.previous_time=None; self.load_sum=0.; self.load_n=0; self.pending_load_sum=0.; self.pending_load_n=0; self.serial=0
    def at(self,event, observe=True):
        t=float(event['posted_at']); source=str(event.get('source','unknown'))
        if self.last is not None and t<self.last: raise ValueError('Feature events must be chronological')
        if self.last is None or t>self.last:
            self.previous_time=self.last
            for posting,app in self.current_posts:
                for window in self.windows.values(): window.append((posting,app))
                self.source_counts[app]+=1
            self.current_posts=[]
            self.load_sum+=self.pending_load_sum; self.load_n+=self.pending_load_n
            self.pending_load_sum=0.; self.pending_load_n=0
        # Strictly earlier outcomes only; same-second ordering is not known.
        while self.pending and self.pending[0][0]<t:
            _,_,s,d=heapq.heappop(self.pending); self.user.add(d); self.sources[s].add(d)
        for minutes,window in self.windows.items():
            while window and window[0][0]<t-minutes*60:
                _,app=window.popleft()
                if minutes==30:
                    self.source_counts[app]-=1
                    if self.source_counts[app]==0: del self.source_counts[app]
        counts={f'count_{m}m':len(window) for m,window in self.windows.items()}
        ref=self.load_sum/self.load_n if self.load_n else np.nan
        sm=self.sources[source]
        result={c:event.get(c,np.nan) for c in META}; result['source']=source
        result.update(counts,distinct_sources=len(self.source_counts),since_previous=t-self.previous_time if self.previous_time is not None else np.nan,load_reference=ref,load_deviation=counts['count_15m']-ref,missing_load_history=int(self.load_n==0),source_median=sm.value(),source_history_count=len(sm),user_median=self.user.value(),user_history_count=len(self.user),missing_outcome_history=int(len(self.user)==0))
        if observe:
            self.current_posts.append((t,source)); self.last=t; self.pending_load_sum+=counts['count_15m']; self.pending_load_n+=1
            r=event.get('removed_at',np.nan)
            if pd.notna(r) and float(r)>=t:
                self.serial+=1; heapq.heappush(self.pending,(float(r),self.serial,source,float(r)-t))
        return result

def build_features(events):
    states=defaultdict(FeatureState); values={}
    for i,row in events.sort_values(['posted_at','episode_id']).iterrows():
        values[i]=states[str(row.participant)].at(row.to_dict())
    return pd.DataFrame.from_dict(values,orient='index').reindex(events.index)[COLUMNS]

def inference_features(event,history):
    state=FeatureState()
    for row in sorted(history,key=lambda x:(x['posted_at'],x.get('episode_id',''))):
        if str(row['participant'])==str(event['participant']) and row['posted_at']<event['posted_at']:
            state.at(row)
    return pd.DataFrame([state.at(event,observe=False)])[COLUMNS]
