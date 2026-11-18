"""Knowledge agent: only authorized retrieval results become context."""
from kb.search_gate import search as kb_search


def handle(question, user, previous):
    hits = kb_search(question, user, top_k=3)
    if not hits:
        return '没有找到您有权限访问的相关文档。'
    return '\n\n'.join(f"来源 {h['path']} {' > '.join(h['section_path'])}：{h['text'][:450]}" for h in hits)
