"""Build the retriever from authorized documents only, before ranking."""
import fnmatch
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAG = ROOT / '../rag-eval'
_cache = {}


def permitted(path, scopes):
    # Paths are corpus-relative, always slash-delimited, and cannot escape the corpus.
    if path.startswith('/') or '\\' in path or any(x in ('.', '..') for x in path.split('/')):
        return False
    return any(fnmatch.fnmatchcase(path, pattern) for pattern in scopes)


def search(query, user, top_k=3, path=None):
    scopes = user.get('kb_scope', [])
    if path is not None and not permitted(path, scopes):
        return []
    if top_k < 1:
        raise ValueError('top_k must be positive')
    key = (tuple(sorted(scopes)), path)
    if key not in _cache:
        sys.path.insert(0, str(RAG.resolve()))
        old = sys.dont_write_bytecode
        try:
            sys.dont_write_bytecode = True
            from ingest import load_documents
            from chunkers import chunk
            from retriever import Retriever
        finally:
            sys.dont_write_bytecode = old
        # Filter the documents BEFORE chunk creation, indexing, scoring, or model context.
        docs = [d for d in load_documents() if permitted(d['path'], scopes) and (path is None or d['path'] == path)]
        if not docs:
            return []
        chunks = chunk(docs, strategy='recursive')
        out = ROOT / 'out'
        out.mkdir(exist_ok=True)
        digest = hashlib.sha256(json.dumps(key).encode()).hexdigest()[:16]
        _cache[key] = Retriever(chunks, out / f'kb-{digest}.sqlite')
    return _cache[key].search(query, top_k=top_k)['hits']
