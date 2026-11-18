"""Route and execute subtasks sequentially in the order asked."""
from registry import AgentRegistry
from router import MockRouter


class Orchestrator:
    def __init__(self, registry=None, router=None):
        self.registry = registry or AgentRegistry()
        self.router = router or MockRouter(self.registry)

    def chat(self, question, user):
        decision = self.router.route(question)
        if decision['kind'] == 'clarify':
            return {'decision':decision, 'clarify':True, 'answer':decision['rewrite'], 'results':[]}
        results = []
        for task in decision['sub_tasks']:
            target = task['target']
            answer = self.registry.dispatch(target, task['question'], user, results)
            results.append({'agent':target, 'cn_name':self.registry.agents[target]['cn_name'], 'answer':answer})
        return {'decision':decision, 'clarify':False, 'answer':'\n\n'.join(r['answer'] for r in results), 'results':results}
