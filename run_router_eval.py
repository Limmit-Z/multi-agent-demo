"""Evaluate configured routing on the unmodified labeled dataset."""
import argparse
import json
from collections import Counter
from pathlib import Path
from registry import AgentRegistry
from router import MockRouter, OpenAICompatibleRouter

ROOT = Path(__file__).resolve().parent
LABELS = ['product_consult','order_query','after_sales','kb','ambiguous']


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--router', choices=['mock','openai-compatible'], default='mock')
    args = parser.parse_args()
    registry = AgentRegistry()
    router = MockRouter(registry) if args.router == 'mock' else OpenAICompatibleRouter(registry)
    with (ROOT / 'data/router_eval.jsonl').open(encoding='utf-8') as f:
        questions = [json.loads(line) for line in f if line.strip()]
    counts, errors = Counter(), []
    for item in questions:
        result = router.route(item['question'])
        routed = 'ambiguous' if result['kind'] == 'clarify' else ('kb' if result.get('target') == 'kb_agent' else result.get('target') or 'complex')
        counts[item['expected'],routed] += 1
        if item['expected'] != routed:
            errors.append((item, routed, result))
    correct = sum(value for (expected, actual), value in counts.items() if expected == actual)
    accuracy = correct / len(questions) if questions else 0
    columns = LABELS + sorted({actual for _, actual in counts if actual not in LABELS})
    lines = ['# 路由评测', '', f'总体准确率：{correct}/{len(questions)} = {accuracy:.2%}', '',
             '| expected \\ routed | ' + ' | '.join(columns) + ' |', '|---|' + '---:|'*len(columns)]
    for expected in LABELS:
        lines.append('| ' + expected + ' | ' + ' | '.join(str(counts[expected, actual]) for actual in columns) + ' |')
    lines += ['', '## 错题与原因', '']
    if not errors:
        lines.append('无错题。')
    for item, routed, result in errors:
        lines.append(f"- {item['qid']}：{item['question']}；期望 {item['expected']}，实际 {routed}；参考说明：{item.get('note','')}；路由决策：{json.dumps(result,ensure_ascii=False)}")
    out = ROOT / 'out'
    out.mkdir(exist_ok=True)
    (out / 'router_eval.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    print(f'路由准确率：{correct}/{len(questions)} = {accuracy:.2%}')
    print(f'错题：{len(errors)}；混淆表：out/router_eval.md')


if __name__ == '__main__':
    main()
