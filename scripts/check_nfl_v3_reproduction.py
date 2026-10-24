"""Compare fresh-source refit with committed evidence; no fitting to a target."""
import json,math,sys
from pathlib import Path

def same(a,b,path=''):
    if isinstance(a,dict):
        assert set(a)==set(b),(path,'keys')
        for k in a:same(a[k],b[k],path+'/'+k)
    elif isinstance(a,list):
        assert len(a)==len(b),(path,'length')
        for i,(x,y) in enumerate(zip(a,b)):same(x,y,path+'/'+str(i))
    elif isinstance(a,float):assert math.isclose(a,b,rel_tol=1e-9,abs_tol=1e-10),(path,a,b)
    else:assert a==b,(path,a,b)

if __name__=='__main__':
    expected,actual=map(Path,sys.argv[1:])
    for filename in ['validation.json','coefficients.json']:
        a,b=[json.loads((p/filename).read_text()) for p in (expected,actual)]
        same(a,b)
    print('Fresh-source reproduction passed: coefficients, source hashes, all season metrics, calibration and weekly memberships.')
