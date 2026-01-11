import requests
from .config import settings
from datetime import datetime


def get_wallet_first_tx_timestamp(wallet_address):
    """Use Etherscan API to get first transaction timestamp for the address.
    Returns unix timestamp (int) or None if unknown.
    """
    if not settings.ETHERSCAN_API_KEY:
        return None
    params = {
        'module': 'account',
        'action': 'txlist',
        'address': wallet_address,
        'startblock': 0,
        'endblock': 99999999,
        'sort': 'asc',
        'apikey': settings.ETHERSCAN_API_KEY
    }
    try:
        r = requests.get(settings.ETHERSCAN_API_URL, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        if data.get('status') == '1' and data.get('result'):
            first = data['result'][0]
            ts = int(first['timeStamp'])
            return ts
    except Exception as e:
        print('Error fetching Etherscan data', e)
    return None


def is_wallet_new(wallet_address, within_seconds=24*3600):
    ts = get_wallet_first_tx_timestamp(wallet_address)
    if ts is None:
        return False
    now = int(datetime.utcnow().timestamp())
    return (now - ts) < within_seconds
