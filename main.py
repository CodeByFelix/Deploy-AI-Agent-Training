#pip fastapi pydantic uvicorn

from fastapi import FastAPI
from pydantic import BaseModel
from agent import chat

class UserRequest (BaseModel):
    query:str
    thread_id:str

class AI_Response (BaseModel):
    AI_Response:str

app = FastAPI ()

@app.post ("/chat", response_model=AI_Response)
async def chatResponse (userRequest:UserRequest):
    query = userRequest.query
    thread_id = userRequest.thread_id

    response = chat (query=query, thread_id=thread_id)
    res = AI_Response (AI_Response=response)
    #return {"AI_Response": response}
    return res



#127.0.0.1:8000/chat#