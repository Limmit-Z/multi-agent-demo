from fastapi.testclient import TestClient
from agents.order_query import handle
from auth.sessions import Sessions
from kb.search_gate import permitted, search
import app


def test_cross_user_order_is_indistinguishable_from_missing():
    bob = Sessions().users['bob']
    assert handle('ORD-1001 状态', bob, []) == '没有找到您的相关订单'
    assert handle('ORD-9999 状态', bob, []) == '没有找到您的相关订单'
    assert 'ORD-1002' in handle('ORD-1002 状态', bob, [])


def test_unauthorized_document_never_in_candidates():
    bob = Sessions().users['bob']
    assert not permitted('guide/best-practices/performance.md', bob['kb_scope'])
    assert search('性能', bob, path='guide/best-practices/performance.md') == []
    hits = search('reactive', bob, top_k=3)
    assert hits and all(permitted(hit['path'], bob['kb_scope']) for hit in hits)


def test_session_expiration_and_client_cannot_set_identity(monkeypatch):
    now = [100.0]
    sessions = Sessions(ttl=1800, clock=lambda: now[0])
    monkeypatch.setattr(app, 'sessions', sessions)
    client = TestClient(app.app)
    token = client.post('/login', json={'user_id':'bob'}).json()['session_id']
    assert token not in str(sessions._sessions)
    assert client.post('/chat', json={'session_id':token,'user_id':'alice','question':'我的订单'}).status_code == 400
    assert client.post('/chat', json={'session_id':token,'question':'ORD-1001 状态'}).json()['answer'] == '没有找到您的相关订单'
    now[0] += 1800
    assert client.post('/chat', json={'session_id':token,'question':'我的订单'}).status_code == 401


def test_login_unknown_user_and_chat_bad_session():
    client = TestClient(app.app)
    assert client.post('/login', json={'user_id':'unknown'}).status_code == 401
    assert client.post('/chat', json={'session_id':'bad','question':'我的订单'}).status_code == 401
