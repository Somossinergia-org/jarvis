import os, sys
sys.path.insert(0, '.')
from dotenv import load_dotenv
load_dotenv()
import httpx

key = os.getenv('ELEVENLABS_API_KEY','')
print('KEY:', key[:15]+'...' if key else 'NO KEY')

r = httpx.get('https://api.elevenlabs.io/v1/voices', headers={'xi-api-key': key})
print('STATUS:', r.status_code)
if r.status_code == 200:
    for v in sorted(r.json()['voices'], key=lambda x: x['name']):
        l = v.get('labels',{})
        if l.get('gender') == 'male':
            print(f"{v['name']:22} | {v['voice_id']} | {l.get('accent','-')}")
else:
    print(r.text[:400])
