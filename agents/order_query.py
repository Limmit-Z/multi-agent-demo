"""Filter by authenticated user before matching an order."""
import json
import re
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / 'data/orders.json'


def order_lookup(question, user):
    orders = json.loads(DATA.read_text(encoding='utf-8'))
    own = [item for item in orders if item['user_id'] == user['user_id']]
    match = re.search(r'ORD-\d+', question, re.I)
    if match:
        own = [item for item in own if item['order_id'].lower() == match.group().lower()]
    else:
        skus = {'笔记':'aurora-notes', '云盘':'aurora-drive', '日历':'aurora-calendar'}
        requested = [sku for name, sku in skus.items() if name in question]
        if requested:
            own = [item for item in own if item['sku'] in requested]
    return own


def handle(question, user, previous):
    own = order_lookup(question, user)
    if not own:
        return '没有找到您的相关订单'
    return '\n'.join(f"{o['order_id']}：{o['plan']}，{o['status']}；{o['detail']}。" for o in own)
