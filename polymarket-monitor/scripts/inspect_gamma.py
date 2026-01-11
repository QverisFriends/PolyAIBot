import requests, json

url = 'https://gamma-api.polymarket.com/'
queries = [
    'query { markets(limit:5) { id title state } }',
    'query { markets(limit:5) { id title tags } }',
    'query { markets(limit:5) { id title description } }',
    'query { fills(limit:5) { id txHash trader amountUsd market { id title } createdAt } }',
    'query { fills(limit:5) { txHash trader amountUsd market { id title } } }',
    'query { trades(limit:5) { id txHash wallet amount market { id title } timestamp } }',
    'query { trades(limit:5) { txHash actor amount outcome { market { id title } } timestamp } }',
    'query { markets(first:5) { id title } }'
]

for q in queries:
    print('\n--- QUERY:')
    print(q)
    try:
        r = requests.post(url, json={'query': q}, timeout=10)
        print('HTTP', r.status_code)
        j = r.json()
        print('keys:', list(j.keys()))
        if 'errors' in j:
            print('errors:', j['errors'])
        if 'data' in j:
            print('data (short):')
            s = json.dumps(j['data'], ensure_ascii=False)
            print(s[:1200])
    except Exception as e:
        print('exception:', e)
