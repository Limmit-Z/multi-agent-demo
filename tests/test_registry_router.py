import json
from pathlib import Path
from registry import AgentRegistry
from router import MockRouter
from orchestrator import Orchestrator


def test_register_fifth_agent_by_config_only(tmp_path):
    items = json.loads((Path(__file__).resolve().parents[1] / 'agents.json').read_text(encoding='utf-8'))
    items.append({'name':'demo_agent','cn_name':'演示','description':'额外智能体', 'tools':[],
                  'examples':['演示词'], 'patterns':['演示词'], 'priority':110,
                  'handler':'agents.product_consult:handle'})
    config = tmp_path / 'agents.json'
    config.write_text(json.dumps(items,ensure_ascii=False),encoding='utf-8')
    registry = AgentRegistry(config)
    assert MockRouter(registry).route('演示词')['target'] == 'demo_agent'
    result = Orchestrator(registry).chat('演示词', {'user_id':'alice'})
    assert result['results'][0]['agent'] == 'demo_agent'


def test_technical_boundary_and_ambiguous():
    router = MockRouter(AgentRegistry())
    assert router.route('ref 和 reactive 怎么选，出故障怎么办？')['target'] == 'kb_agent'
    assert router.route('它和那个有什么区别？')['kind'] == 'clarify'


def test_complex_preserves_subtask_order():
    result = MockRouter(AgentRegistry()).route('我的 ORD-1002 开通了吗？顺便说说极光云盘的续费政策')
    assert result['kind'] == 'complex'
    assert [t['target'] for t in result['sub_tasks']] == ['order_query','product_consult']
