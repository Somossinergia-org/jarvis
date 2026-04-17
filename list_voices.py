import urllib.request, json
req = urllib.request.Request(
    'https://api.elevenlabs.io/v1/voices',
    headers={'xi-api-key':'sk_2fdd11d488c130eb6d04d90f57fdeb238e47aad903f7e833'}
)
with urllib.request.urlopen(req) as r:
    voices = json.loads(r.read())['voices']
print("=== Voces masculinas disponibles ===")
for v in sorted(voices, key=lambda x: x['name']):
    labels = v.get('labels', {})
    if labels.get('gender') == 'male':
        print(f"{v['name']:20} | {v['voice_id']} | accent:{labels.get('accent','-')} | age:{labels.get('age','-')} | use:{labels.get('use case','-')}")
