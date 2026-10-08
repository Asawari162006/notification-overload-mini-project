import numpy as np
import pandas as pd

class Baseline:
    def __init__(self,historical=False): self.historical=historical
    def fit(self,X,y):
        self.median=float(np.median(y)); self.source=pd.DataFrame({'source':X.source.to_numpy(),'y':np.asarray(y)}).groupby('source').y.median().to_dict(); return self
    def predict(self,X):
        if not self.historical: return np.full(len(X),self.median)
        # Identical posting-cutoff outcome updates for all models. Use personal,
        # then own source history, then frozen training source/global fallbacks.
        return X.user_median.fillna(X.source_median).fillna(X.source.map(self.source)).fillna(self.median).to_numpy()
