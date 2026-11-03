"""Reject modifications/deletions of any saved audit file except latest.json."""
import subprocess,sys
from pathlib import Path
root=Path(sys.argv[1] if len(sys.argv)>1 else 'state')
changed=subprocess.check_output(['git','-C',str(root),'diff','--name-status','HEAD']).decode().splitlines()
for line in changed:
    status,path=line.split('\t',1)
    if status!='A' and path!='latest.json':raise SystemExit('Immutable state change rejected: '+line)
print('Existing audit files unchanged')
