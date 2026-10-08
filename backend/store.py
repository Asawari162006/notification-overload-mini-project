"""SQLite simulator. Virtual time and policy snapshots survive restarts."""
import json
from sqlalchemy import create_engine,Column,String,Integer,Float,Text,select
from sqlalchemy.orm import DeclarativeBase,sessionmaker
from ml.data import ROOT

class Base(DeclarativeBase): pass
class Item(Base):
    __tablename__='items'
    key=Column(String,primary_key=True); source=Column(String,nullable=False); title=Column(String,nullable=False)
    posted_at=Column(Float,nullable=False); due=Column(Float,nullable=False); deadline=Column(Float,nullable=False)
    delivered_at=Column(Float); status=Column(String,nullable=False); digest=Column(String); mode=Column(String,nullable=False)
class Setting(Base):
    __tablename__='settings'; key=Column(String,primary_key=True); value=Column(Text,nullable=False)

DEFAULT={'protected_sources':['demo.emergency'],'digest_interval_seconds':300,'maximum_delay_seconds':120}
class Store:
    def __init__(self,url=None):
        self.engine=create_engine(url or f'sqlite:///{ROOT / "data/simulator.db"}',connect_args={'check_same_thread':False},future=True)
        Base.metadata.create_all(self.engine); self.Session=sessionmaker(self.engine,expire_on_commit=False)
        with self.Session.begin() as s:
            if s.get(Setting,'preferences') is None: s.add(Setting(key='preferences',value=json.dumps(DEFAULT)))
            if s.get(Setting,'clock') is None: s.add(Setting(key='clock',value='0'))
    def preferences(self,value=None):
        with self.Session.begin() as s:
            row=s.get(Setting,'preferences')
            if value is not None: row.value=json.dumps(value)
            return json.loads(row.value)
    def snapshot(self):
        with self.Session() as s:
            rows=s.scalars(select(Item).order_by(Item.posted_at,Item.key)).all()
            fields=['key','source','title','posted_at','due','deadline','delivered_at','status','digest','mode']
            clock=float(s.get(Setting,'clock').value)
            items=[{f:getattr(r,f) for f in fields} for r in rows]
            for item in items:
                if item['delivered_at'] is not None and item['delivered_at']>clock:
                    item['delivered_at']=None; item['status']='scheduled_protected'
            delivered=[r for r in rows if r.delivered_at is not None and r.delivered_at<=clock]
            return {'clock':float(s.get(Setting,'clock').value),'items':items,'preferences':json.loads(s.get(Setting,'preferences').value),'alerts':sum(r.status=='protected' or r.status=='deadline' or r.status=='manual' for r in delivered)+len({r.digest for r in delivered if r.digest}),'delivered_items':len(delivered),'immediate_policy_reference_alerts':len(delivered),'mean_delay_seconds':sum((r.delivered_at-r.posted_at) for r in delivered)/max(1,len(delivered))}
    def ingest(self,data):
        with self.Session.begin() as s:
            if s.get(Item,data['key']) is not None: return self.snapshot()
            clock=float(s.get(Setting,'clock').value)
            if data['posted_at']<clock: raise ValueError('Ingestion cannot precede virtual clock; reset or choose current time')
            p=json.loads(s.get(Setting,'preferences').value); t=data['posted_at']; interval=p['digest_interval_seconds']; due=(int(t//interval)+1)*interval; deadline=t+p['maximum_delay_seconds']; protected=data['source'] in p['protected_sources']
            s.add(Item(**data,due=t if protected else due,deadline=t if protected else deadline,status='protected' if protected else 'deferred',delivered_at=t if protected else None))
        return self.snapshot()
    def advance(self,t):
        with self.Session.begin() as s:
            current=float(s.get(Setting,'clock').value)
            if t<current: raise ValueError('Clock must be monotonic')
            for r in s.scalars(select(Item).where(Item.delivered_at.is_(None)).order_by(Item.posted_at,Item.key)):
                trigger=min(r.deadline,r.due)
                if trigger<=t:
                    r.delivered_at=trigger
                    if r.deadline<=r.due: r.status='deadline'
                    else: r.status='digest'; r.digest=f'{r.mode}:digest:{r.due:.0f}'
            s.get(Setting,'clock').value=str(t)
        return self.snapshot()
    def deliver(self,key):
        with self.Session.begin() as s:
            r=s.get(Item,key)
            if r is None: raise KeyError(key)
            clock=float(s.get(Setting,'clock').value)
            if r.posted_at>clock: raise ValueError('Item is in the virtual future')
            if r.delivered_at is None: r.delivered_at=clock; r.status='manual'
        return self.snapshot()
    def reset(self):
        with self.Session.begin() as s:
            for r in s.scalars(select(Item)): s.delete(r)
            s.get(Setting,'clock').value='0'
        return self.snapshot()
