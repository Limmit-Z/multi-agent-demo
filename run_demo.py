"""Run ten representative questions through the actual orchestrator."""
import argparse
import json
from pathlib import Path
from auth.sessions import Sessions
from orchestrator import Orchestrator
from registry import AgentRegistry
from router import MockRouter, OpenAICompatibleRouter

ROOT = Path(__file__).resolve().parent
CASES = [
    ('alice','极光笔记团队版多少钱？',['product_consult']),
    ('bob','我的 ORD-1002 开通了吗？',['order_query']),
    ('alice','激活码没收到怎么办？',['after_sales']),
    ('alice','ref 和 reactive 怎么选？',['kb_agent']),
    ('bob','我的 ORD-1002 开通了吗？顺便说说极光云盘的续费政策',['order_query','product_consult']),
    ('alice','这个产品怎么样？',[]),
    ('bob','极光云盘外链能设水印吗？',['product_consult']),
    ('bob','发票怎么开？',['after_sales']),
    ('alice','我的 ORD-1001 什么状态？',['order_query']),
    ('bob','v-for 的 key 有什么作用？',['kb_agent']),
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--router', choices=['mock','openai-compatible'], default='mock')
    args = parser.parse_args()
    registry = AgentRegistry()
    router = MockRouter(registry) if args.router == 'mock' else OpenAICompatibleRouter(registry)
    orchestrator, sessions = Orchestrator(registry, router), Sessions()
    out = ROOT / 'out'
    out.mkdir(exist_ok=True)
    rows = []
    with (out / 'trace.jsonl').open('w', encoding='utf-8') as trace:
        for index, (user_id, question, expected) in enumerate(CASES, 1):
            token = sessions.login(user_id)
            result = orchestrator.chat(question, sessions.get_user(token))
            names = [item['agent'] for item in result['results']]
            success = names == expected and result['clarify'] == (not expected) and bool(result['answer'])
            row = {'id':index,'question':question,'decision':result['decision'],'agents':names,
                   'clarify':result['clarify'],'success':success}
            rows.append(row)
            trace.write(json.dumps({**row, 'results':result['results'], 'answer':result['answer']},ensure_ascii=False)+'\n')
            print(f"{index:02}: kind={result['decision']['kind']} agents={','.join(names) or '-'} clarify={result['clarify']} success={success}")
    summary = {'total':len(rows),'successes':sum(r['success'] for r in rows),
               'complex_count':sum(r['decision']['kind']=='complex' for r in rows),
               'clarify_count':sum(r['clarify'] for r in rows),'cases':rows}
    (out / 'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f"成功 {summary['successes']}/{summary['total']}；复合题 {summary['complex_count']}；澄清 {summary['clarify_count']}")


if __name__ == '__main__':
    main()
