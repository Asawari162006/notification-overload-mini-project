from importlib.metadata import distribution,version
from packaging.requirements import Requirement
from pathlib import Path
roots=['fastapi','uvicorn','pydantic','httpx','pandas','numpy','scikit-learn','SQLAlchemy','pytest','joblib','matplotlib']
seen={};pending=roots[:]
while pending:
 name=pending.pop();key=name.lower().replace('_','-')
 if key in seen:continue
 d=distribution(name);seen[key]=(d.metadata['Name'],d.version)
 for dep in d.requires or []:
  r=Requirement(dep)
  if r.marker is None or r.marker.evaluate({'extra':''}):pending.append(r.name)
Path('requirements.lock.txt').write_text('# Exact tested dependency closure on Python 3.13 / Windows. Primary pins: requirements.txt.\n'+'\n'.join(f'{n}=={v}' for n,v in sorted(seen.values(),key=lambda x:x[0].lower()))+'\n',encoding='utf8')
