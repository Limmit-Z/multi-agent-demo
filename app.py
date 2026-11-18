"""HTTP interface; authorization is always resolved server-side."""
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from auth.sessions import Sessions
from orchestrator import Orchestrator

app = FastAPI(title='极光办公演示')
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['GET','POST'], allow_headers=['Content-Type'])
sessions = Sessions()
orchestrator = Orchestrator()


@app.post('/login')
def login(body: dict = Body(...)):
    token = sessions.login(body.get('user_id'))
    if token is None:
        raise HTTPException(status_code=401, detail='未知演示账号')
    return {'session_id':token, 'expires_in':sessions.ttl}


@app.post('/chat')
def chat(body: dict = Body(...)):
    if 'user_id' in body:
        raise HTTPException(status_code=400, detail='请求体不得包含 user_id')
    user = sessions.get_user(body.get('session_id'))
    if user is None:
        raise HTTPException(status_code=401, detail='会话无效或已过期')
    question = body.get('question')
    if not isinstance(question, str) or not question.strip():
        raise HTTPException(status_code=400, detail='问题不能为空')
    return orchestrator.chat(question.strip(), user)


@app.get('/agents')
def agents():
    return {'agents':orchestrator.registry.list_agents()}
