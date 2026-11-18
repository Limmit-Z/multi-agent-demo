"""Configuration-driven agent registration and handler loading."""
import importlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


class AgentRegistry:
    def __init__(self, config_path=None):
        self.agents = {}
        with Path(config_path or ROOT / 'agents.json').open(encoding='utf-8') as f:
            for item in json.load(f):
                self.register(item)

    def register(self, item):
        required = ('name', 'cn_name', 'description', 'tools', 'examples', 'patterns', 'handler')
        if any(key not in item for key in required) or item['name'] in self.agents:
            raise ValueError('invalid or duplicate agent registration')
        self.agents[item['name']] = dict(item)

    def list_agents(self):
        return [{key: value for key, value in item.items() if key not in ('handler', 'patterns', 'priority')}
                for item in self.agents.values()]

    def dispatch(self, name, question, user, previous=None):
        item = self.agents[name]
        module, function = item['handler'].split(':', 1)
        handler = getattr(importlib.import_module(module), function)
        return handler(question, user, previous or [])
