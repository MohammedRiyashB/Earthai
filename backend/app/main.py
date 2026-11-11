import json, uuid
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from .config import APP_NAME, MODE, MODEL, ORIGINS, BASE_URL
from .db import init, all_rows, run
from .engine import generate

app = FastAPI(title=APP_NAME, version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=ORIGINS, allow_credentials=False, allow_methods=["*"], allow_headers=["*"])
def stamp(): return datetime.now(timezone.utc).isoformat()

@app.on_event("startup")
def startup(): init()

@app.get("/api/health")
def health(): return {"status":"ok","app":APP_NAME,"mode":MODE,"model":MODEL,"model_configured":MODE=="mock" or bool(BASE_URL)}

@app.get("/api/chats")
def chats(): return all_rows("SELECT * FROM chats ORDER BY updated_at DESC")

@app.post("/api/chats")
def create_chat(body: dict):
    cid, t = str(uuid.uuid4()), stamp()
    title = str(body.get("title","New chat"))[:80]
    run("INSERT INTO chats VALUES(?,?,?,?)",(cid,title,t,t))
    return {"id":cid,"title":title,"created_at":t,"updated_at":t}

@app.get("/api/chats/{cid}/messages")
def messages(cid: str):
    if not all_rows("SELECT id FROM chats WHERE id=?",(cid,)): raise HTTPException(404,"Chat not found")
    return all_rows("SELECT * FROM messages WHERE chat_id=? ORDER BY created_at",(cid,))

@app.delete("/api/chats/{cid}")
def delete_chat(cid: str):
    run("DELETE FROM messages WHERE chat_id=?",(cid,))
    run("DELETE FROM chats WHERE id=?",(cid,))
    return {"deleted":True}

@app.post("/api/chat/stream")
async def chat(body: dict):
    cid, prompt = body.get("chat_id"), str(body.get("message","")).strip()
    if not cid or not prompt: raise HTTPException(400,"chat_id and message are required")
    found = all_rows("SELECT * FROM chats WHERE id=?",(cid,))
    if not found: raise HTTPException(404,"Chat not found")
    if len(prompt)>30000: raise HTTPException(413,"Message too long")
    t, uid, aid = stamp(), str(uuid.uuid4()), str(uuid.uuid4())
    if found[0]["title"]=="New chat": run("UPDATE chats SET title=?,updated_at=? WHERE id=?",(prompt.replace("\n"," ")[:48],t,cid))
    run("INSERT INTO messages VALUES(?,?,?,?,?)",(uid,cid,"user",prompt,t))
    history=[]
    for m in body.get("history",[])[-20:]:
        if m.get("role") in ("user","assistant") and isinstance(m.get("content"),str): history.append({"role":m["role"],"content":m["content"][:30000]})
    history.append({"role":"user","content":prompt})
    async def events():
        parts=[]
        try:
            async for token in generate(history):
                parts.append(token)
                yield "data: "+json.dumps({"token":token})+"\n\n"
            run("INSERT INTO messages VALUES(?,?,?,?,?)",(aid,cid,"assistant","".join(parts),stamp()))
            run("UPDATE chats SET updated_at=? WHERE id=?",(stamp(),cid))
            yield "data: "+json.dumps({"done":True,"message_id":aid})+"\n\n"
        except Exception as e: yield "data: "+json.dumps({"error":str(e)})+"\n\n"
        yield "data: [DONE]\n\n"
    return StreamingResponse(events(),media_type="text/event-stream",headers={"Cache-Control":"no-cache","X-Accel-Buffering":"no"})
