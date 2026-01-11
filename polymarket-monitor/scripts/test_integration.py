import asyncio
import json
import requests
from src.polymarket_monitor.adapter import get_adapter
from src.polymarket_monitor.config import settings
from src.polymarket_monitor.blockchain import get_wallet_first_tx_timestamp, is_wallet_new
from src.polymarket_monitor.alerts import send_alert_email

async def main():
    print("POLY_SOURCE_TYPE:", settings.POLY_SOURCE_TYPE)
    print("POLY_SOURCE_URL:", settings.POLY_SOURCE_URL)
    print("POLY_MARKET_KEYWORDS:", settings.POLY_MARKET_KEYWORDS)
    print("POLY_GRAPHQL_TRADES_QUERY set:", bool(settings.POLY_GRAPHQL_TRADES_QUERY))

    adapter = get_adapter()
    print("Using adapter:", adapter.__class__.__name__)

    trades = []
    try:
        trades = await adapter.fetch_recent_trades()
    except Exception as e:
        print("Error fetching trades:", e)

    print("Fetched trades count:", len(trades) if trades is not None else 'None')
    for i, t in enumerate(trades[:10]):
        print(f"--- Trade {i+1} ---")
        print(json.dumps(t, indent=2, ensure_ascii=False))

    # Raw GraphQL POST test to inspect errors / auth requirements
    if settings.POLY_SOURCE_URL:
        endpoint = settings.POLY_SOURCE_URL
        if endpoint.endswith('/'):
            endpoint = endpoint + 'query'
        elif not endpoint.endswith('/query'):
            endpoint = endpoint + '/query'
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

        print('\nPerforming raw POST to GraphQL endpoint (to inspect auth/errors):')
        try:
            resp = requests.post(endpoint, json={'query': 'query { markets(limit:1) { id title } }'}, headers=headers, timeout=10)
            print('HTTP', resp.status_code)
            try:
                print('JSON:', json.dumps(resp.json(), ensure_ascii=False, indent=2)[:2000])
            except Exception:
                print('Text:', resp.text[:2000])
        except Exception as e:
            print('Raw POST error:', e)

    if trades:
        # test Etherscan lookup on first trade's wallet
        first_wallet = trades[0].get('wallet')
        print("Testing wallet chain history for:", first_wallet)
        try:
            ts = get_wallet_first_tx_timestamp(first_wallet)
            print("First tx timestamp:", ts)
            print("Is wallet new (<24h):", is_wallet_new(first_wallet))
        except Exception as e:
            print("Etherscan check error:", e)

    # Test email send (will skip if SMTP not configured)
    print("Testing alert email (may be skipped if SMTP not configured)")
    try:
        send_alert_email('0xTESTWALLET000000000000000000000000', 12345, 'Integration Test Market', '测试告警：integration-test')
    except Exception as e:
        print('Error sending test email:', e)

if __name__ == '__main__':
    asyncio.run(main())
