import asyncio
import aiohttp
import time
import requests
from .config import settings

class BaseAdapter:
    async def fetch_recent_trades(self):
        """Return an iterable of trade dicts with keys:
           tx_hash, wallet, market_id, market_name, amount_usdc, timestamp
        """
        raise NotImplementedError

class MockAdapter(BaseAdapter):
    async def fetch_recent_trades(self):
        # Return empty list for now; used for testing
        return []

class RestAdapter(BaseAdapter):
    def __init__(self, url):
        self.url = url

    async def fetch_recent_trades(self):
        # This is a generic placeholder - user should provide real endpoint
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(self.url, timeout=10) as resp:
                    data = await resp.json()
                    # User must map data -> expected trade dicts
                    # Here we assume data is list of trades already matching our keys
                    return data
            except Exception as e:
                print('Error fetching trades from rest adapter', e)
                return []

class PolymarketGammaAdapter(BaseAdapter):
    """A GraphQL adapter tuned to Polymarket's Gamma API.
    It will try a configurable query from env var `POLY_GRAPHQL_TRADES_QUERY`,
    otherwise it attempts several common trade queries and maps fields into
    the internal trade dict format.
    """
    def __init__(self, url):
        self.url = url

    async def _post(self, session, query, variables=None):
        payload = {'query': query}
        if variables:
            payload['variables'] = variables

        # Build headers from config (auth header/cookie)
        headers = {}
        if settings.POLY_AUTH_HEADER:
            ah = settings.POLY_AUTH_HEADER
            if ':' in ah:
                k, v = ah.split(':', 1)
                headers[k.strip()] = v.strip()
            else:
                headers['Authorization'] = ah.strip()
        if settings.POLY_AUTH_COOKIE:
            headers['Cookie'] = settings.POLY_AUTH_COOKIE

        # Ensure endpoint points to /query
        endpoint = self.url
        if endpoint.endswith('/'):
            endpoint = endpoint + 'query'
        elif not endpoint.endswith('/query'):
            endpoint = endpoint + '/query'

        # If no explicit cookie provided, try a GET to establish any server-set cookies
        if not settings.POLY_AUTH_COOKIE:
            try:
                await session.get(self.url, timeout=10)
            except Exception:
                pass

        try:
            async with session.post(endpoint, headers=headers or None, json=payload, timeout=15) as resp:
                text = await resp.text()
                try:
                    return await resp.json()
                except Exception:
                    return {'errors': [{'message': 'Non-JSON response', 'status': resp.status, 'text': text[:1000]}]}
        except Exception as e:
            return {'errors': [{'message': f'Network error: {e}'}]}

    def _map_trade(self, item):
        # Flexible mapping for different field names
        tx = item.get('txHash') or item.get('tx_hash') or item.get('id') or item.get('txhash')
        wallet = item.get('trader') or item.get('wallet') or item.get('actor') or item.get('owner')
        amount = item.get('amountUsd') or item.get('amount') or item.get('value') or 0
        market = item.get('market') or item.get('marketId') or {}
        market_id = None
        market_name = None
        if isinstance(market, dict):
            market_id = market.get('id')
            market_name = market.get('title') or market.get('name')
        else:
            market_id = item.get('market_id') or item.get('marketId')
        ts = item.get('createdAt') or item.get('timestamp') or item.get('time')
        try:
            ts = int(ts)
        except Exception:
            ts = int(time.time())
        try:
            amount = float(amount)
        except Exception:
            amount = 0.0
        return {
            'tx_hash': tx,
            'wallet': wallet,
            'market_id': market_id,
            'market_name': market_name,
            'amount_usdc': amount,
            'timestamp': ts
        }

    async def fetch_recent_trades(self):
        async with aiohttp.ClientSession() as session:
            # If user provided a custom query via env, use it
            custom = settings.POLY_GRAPHQL_TRADES_QUERY
            candidate_queries = []
            if custom:
                candidate_queries.append(custom)

            # Common field names used in different schemas
            candidate_queries += [
                '''query { fills(limit:50) { txHash trader amountUsd market { id title } createdAt } }''',
                '''query { fills(limit:50) { id txHash trader amount market { id title name } createdAt } }''',
                '''query { trades(limit:50) { id txHash wallet amount market { id title } timestamp } }''',
                '''query { trades(limit:50) { txHash actor amount outcome { market { id title } } timestamp } }'''
            ]

            for q in candidate_queries:
                try:
                    data = await self._post(session, q)
                except Exception as e:
                    # try next query
                    continue

                if not data or 'data' not in data:
                    continue

                # Find the first list-like value in the data root
                root = data['data']
                list_found = None
                for v in root.values():
                    if isinstance(v, list):
                        list_found = v
                        break

                if not list_found:
                    # maybe nested under a field
                    # try to flatten one more level
                    for v in root.values():
                        if isinstance(v, dict):
                            for vv in v.values():
                                if isinstance(vv, list):
                                    list_found = vv
                                    break
                            if list_found:
                                break

                if not list_found:
                    continue

                # Map items and apply market keyword filter if provided
                keywords = [k.strip().lower() for k in (settings.POLY_MARKET_KEYWORDS or '').split(',') if k.strip()]
                mapped = []
                for item in list_found:
                    t = self._map_trade(item)
                    if keywords and t.get('market_name'):
                        name = (t.get('market_name') or '').lower()
                        if not any(kw in name for kw in keywords):
                            continue
                    mapped.append(t)
                return mapped

            # Fallback empty
            return []

class TheGraphAdapter(BaseAdapter):
    """Adapter to query Polymarket's public subgraph on The Graph or Goldsky."""
    def __init__(self, url):
        self.url = url
        # candidate fallback endpoints to try when default is unavailable
        self.candidates = [
            url,
            # The Graph hosted (may be deprecated) fallbacks
            'https://api.thegraph.com/subgraphs/name/Polymarket/polymarket-subgraph',
            'https://api.thegraph.com/subgraphs/name/polymarket/polymarket-subgraph',
            'https://api.thegraph.com/subgraphs/name/Polymarket/fpmm-subgraph',
            'https://api.thegraph.com/subgraphs/name/polymarket/fpmm-subgraph',
            # Goldsky public endpoints (documented in Polymarket docs)
            'https://api.goldsky.com/api/public/project_cl6mb8i9h0003e201j6li0diw/subgraphs/activity-subgraph/0.0.4/gn',
            'https://api.goldsky.com/api/public/project_cl6mb8i9h0003e201j6li0diw/subgraphs/orderbook-subgraph/0.0.1/gn',
            'https://api.goldsky.com/api/public/project_cl6mb8i9h0003e201j6li0diw/subgraphs/positions-subgraph/0.0.7/gn',
            'https://api.goldsky.com/api/public/project_cl6mb8i9h0003e201j6li0diw/subgraphs/pnl-subgraph/0.0.14/gn'
        ]

    def _post(self, query, variables=None):
        payload = {'query': query}
        if variables:
            payload['variables'] = variables
        last_err = None
        for endpoint in self.candidates:
            if not endpoint:
                continue
            try:
                r = requests.post(endpoint, json=payload, timeout=10)
                # sometimes The Graph returns a 200 with errors, so check json
                try:
                    j = r.json()
                except Exception:
                    j = {'errors': [{'message': f'Non-JSON response: HTTP {r.status_code}'}]}
                # if returned graph data, return
                if 'data' in j and any(isinstance(v, list) for v in j['data'].values()):
                    return j
                # if errors, capture and try next candidate
                last_err = j.get('errors') or [{'message': f'HTTP {r.status_code}'}]
            except Exception as e:
                last_err = [{'message': str(e)}]
        return {'errors': last_err or [{'message': 'No endpoint available'}]}
    async def fetch_recent_trades(self):
        # The activity subgraph exposes several event types (negRiskConversions, splits, merges, redemptions, etc.).
        # Try a set of candidate entity queries and map any returned items to the internal trade dict format.
        candidates = [
            ('negRiskConversions', '''query RecentNegRisk($first:Int){ negRiskConversions(first:$first, orderBy: timestamp, orderDirection: desc) { id stakeholder negRiskMarketId amount timestamp } }'''),
            ('splits', '''query RecentSplits($first:Int){ splits(first:$first, orderBy: timestamp, orderDirection: desc) { id stakeholder condition amount timestamp } }'''),
            ('merges', '''query RecentMerges($first:Int){ merges(first:$first, orderBy: timestamp, orderDirection: desc) { id stakeholder condition amount timestamp } }'''),
            ('redemptions', '''query RecentRedemptions($first:Int){ redemptions(first:$first, orderBy: timestamp, orderDirection: desc) { id redeemer condition payout timestamp } }'''),
        ]

        for name, q in candidates:
            data = self._post(q, {'first': 50})
            if not data or 'data' not in data:
                continue
            items = data['data'].get(name) or []
            if not items:
                continue
            mapped = []
            for it in items:
                try:
                    idv = it.get('id')
                    tx = idv.split('_')[0] if idv and '_' in idv else idv
                    if name == 'negRiskConversions':
                        wallet = it.get('stakeholder')
                        market_id = it.get('negRiskMarketId')
                        amount_raw = it.get('amount') or 0
                    elif name in ('splits', 'merges'):
                        wallet = it.get('stakeholder')
                        market_id = it.get('condition')
                        amount_raw = it.get('amount') or 0
                    elif name == 'redemptions':
                        wallet = it.get('redeemer')
                        market_id = it.get('condition')
                        amount_raw = it.get('payout') or 0
                    else:
                        wallet = None
                        market_id = None
                        amount_raw = 0

                    # Amounts appear to be in integer base units (e.g., 6 decimals for USDC)
                    try:
                        amount = float(int(amount_raw)) / 1e6
                    except Exception:
                        try:
                            amount = float(amount_raw)
                        except Exception:
                            amount = 0.0
                    ts = int(it.get('timestamp') or 0)
                    mapped.append({
                        'tx_hash': tx,
                        'wallet': wallet,
                        'market_id': market_id,
                        'market_name': market_id,
                        'amount_usdc': amount,
                        'timestamp': ts
                    })
                except Exception:
                    continue

            # Apply optional market keyword filter (if configured).
            # If market_name is just an address/id (starts with 0x), treat it as unknown and do NOT drop it
            keywords = [k.strip().lower() for k in (settings.POLY_MARKET_KEYWORDS or '').split(',') if k.strip()]
            if keywords:
                filtered = []
                for t in mapped:
                    name_val_raw = (t.get('market_name') or '')
                    if name_val_raw.startswith('0x'):
                        # unknown human-readable name, include so it won't be dropped
                        filtered.append(t)
                        continue
                    name_val = name_val_raw.lower()
                    if any(kw in name_val for kw in keywords):
                        filtered.append(t)
                if filtered:
                    return filtered
                else:
                    # no matches here; continue to next candidate
                    continue

            return mapped

        # Nothing found
        return []

class GraphQLAdapter(BaseAdapter):
    def __init__(self, url):
        self.url = url

    async def fetch_recent_trades(self):
        # Generic GraphQL adapter - try to use a user-provided query if present
        custom = settings.POLY_GRAPHQL_TRADES_QUERY
        if not custom:
            return []
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(self.url, json={'query': custom}, timeout=10) as resp:
                    data = await resp.json()
                    # Attempt to extract list similarly
                    root = data.get('data') or {}
                    for v in root.values():
                        if isinstance(v, list):
                            # Map with basic mapping
                            mapped = []
                            for item in v:
                                mapped.append({
                                    'tx_hash': item.get('txHash') or item.get('id'),
                                    'wallet': item.get('trader') or item.get('wallet'),
                                    'market_id': (item.get('market') or {}).get('id'),
                                    'market_name': (item.get('market') or {}).get('title'),
                                    'amount_usdc': item.get('amountUsd') or item.get('amount') or 0,
                                    'timestamp': item.get('createdAt') or item.get('timestamp')
                                })
                            return mapped
            except Exception as e:
                print('Error fetching trades from graphql adapter', e)
                return []


def get_adapter():
    t = settings.POLY_SOURCE_TYPE.lower()
    url = settings.POLY_SOURCE_URL
    if t == 'rest' and url:
        return RestAdapter(url)
    if t == 'graphql' and url:
        return PolymarketGammaAdapter(url)
    # New: support The Graph via POLY_SUBGRAPH_URL or when type is 'thegraph'/'subgraph'
    if t in ('thegraph', 'subgraph') or settings.POLY_SUBGRAPH_URL:
        sg = settings.POLY_SUBGRAPH_URL
        if sg:
            return TheGraphAdapter(sg)
    return MockAdapter()
