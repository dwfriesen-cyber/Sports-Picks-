"""Public data downloads with bounded retries and hashed, timestamped source receipts."""
import datetime as dt,hashlib,json,time,urllib.request
from pathlib import Path

class SourceError(RuntimeError): pass

def download(url, path, attempts=3):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    for attempt in range(attempts):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'SportsPicksResearch/1.0 (noncommercial)'})
            with urllib.request.urlopen(req,timeout=45) as response:
                data=response.read()
            if not data:raise SourceError('Empty source response')
            path.write_bytes(data)
            receipt={'url':url,'fetched_at':dt.datetime.now(dt.timezone.utc).isoformat(),'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)}
            path.with_suffix(path.suffix+'.receipt.json').write_text(json.dumps(receipt,indent=2))
            return data
        except Exception as exc:
            if attempt==attempts-1:raise SourceError(f'{url}: {exc}') from exc
            time.sleep(2**attempt)
