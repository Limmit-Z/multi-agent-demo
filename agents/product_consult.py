"""Product catalog consultation."""
import json
import re
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / 'data/catalog.json'


def catalog_search(question):
    catalog = json.loads(DATA.read_text(encoding='utf-8'))
    chosen = [item for item in catalog if item['name'] in question or item['name'].replace('极光', '') in question]
    return chosen or catalog


def handle(question, user, previous):
    chosen = catalog_search(question)
    lines = []
    for item in chosen:
        plans = item['plans']
        named = [p for p in plans if p['plan'] in question]
        comparison = any(word in question for word in ('区别', '差异', '相比', '哪个', '多了什么', '对比'))
        if named and not comparison:
            plans = named
        details = '；'.join(f"{p['plan']} {p['price']}（{p['notes']}）" for p in plans)
        if any(word in question for word in ('价格', '多少钱', '续费', '折扣', '版本', '区别', '相比', '哪个', '买')):
            answer = details
        else:
            answer = f"{item['tagline']}。{details}。{'；'.join(item['faq'])}"
        people = re.search(r'(\d+)\s*人', question)
        if people and item['name'] == '极光笔记':
            count = int(people.group(1))
            answer += f'。团队版每份含 10 席位，{count} 人至少需要 {(count + 9) // 10} 份；请确认实际购买规则'
        lines.append(f"{item['name']}：{answer}。")
    return '\n'.join(lines)
