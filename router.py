"""Config-driven mock routing with explicit technical-document precedence."""
import json
import os
import re
import urllib.request


class MockRouter:
    def __init__(self, registry):
        self.registry = registry

    def _single(self, text):
        if re.search(r'这个产品|帮我处理一下|它和那个|这个怎么', text) or re.fullmatch(r'怎么处理[？?。]?', text.strip()):
            return None
        matches = []
        for item in self.registry.agents.values():
            if any(re.search(pattern, text, re.I) for pattern in item['patterns']):
                matches.append(item)
        # The configured KB technical terms outrank after-sales words such as “怎么办”.
        # Priority is configuration-driven so a newly registered agent needs no router change.
        if matches:
            return max(matches, key=lambda item: item.get('priority', 0))['name']
        return None

    def route(self, question):
        fragments = [part.strip(' ，,。；;？！?!') for part in re.split(r'顺便|另外|同时|再问(?:一下)?', question) if part.strip(' ，,。；;？！?!')]
        tasks = [{'target': self._single(part), 'question': part} for part in fragments]
        if len(tasks) > 1 and all(t['target'] for t in tasks) and len({t['target'] for t in tasks}) > 1:
            return {'kind':'complex', 'target':None, 'sub_tasks':tasks, 'confidence':0.95, 'rewrite':question}
        target = self._single(question)
        if target:
            return {'kind':'single', 'target':target, 'sub_tasks':[{'target':target, 'question':question}], 'confidence':0.9, 'rewrite':question}
        return {'kind':'clarify', 'target':None, 'sub_tasks':[], 'confidence':0.0, 'rewrite':'请说明具体产品、订单或技术问题。'}


class OpenAICompatibleRouter:
    def __init__(self, registry):
        self.registry = registry

    def route(self, question):
        prompt = ('请根据智能体清单路由，输出 JSON：kind 为 single、complex 或 clarify；'
                  'target 为注册名或 null；sub_tasks 是 {target, question} 数组；'
                  '另含 confidence 和 rewrite。智能体清单：' + json.dumps(self.registry.list_agents(), ensure_ascii=False))
        data = {'model':os.environ['MODEL'], 'response_format':{'type':'json_object'},
                'messages':[{'role':'system','content':prompt},{'role':'user','content':question}]}
        request = urllib.request.Request(os.environ['BASE_URL'].rstrip('/')+'/chat/completions',
                   data=json.dumps(data).encode('utf-8'), headers={'Content-Type':'application/json', 'Authorization':'Bearer '+os.environ['API_KEY']})
        with urllib.request.urlopen(request, timeout=30) as response:
            decision = json.loads(json.load(response)['choices'][0]['message']['content'])
        if decision.get('kind') not in ('single','complex','clarify'):
            raise ValueError('invalid routing decision')
        if any(t['target'] not in self.registry.agents for t in decision.get('sub_tasks', [])):
            raise ValueError('unknown routing target')
        if decision['kind'] == 'single' and decision.get('target') not in self.registry.agents:
            raise ValueError('unknown routing target')
        return decision
