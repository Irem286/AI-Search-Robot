from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
from ddgs import DDGS  
app = FastAPI()
import os
# Allow the website to communicate with the Python server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Stores the current conversation
conversation_history = []
def search_web(query):
    results = DDGS().text(query, max_results=5)

    web_text = ""

    for item in results:
        title = item.get("title", "")
        body = item.get("body", "")
        href = item.get("href", "")

        web_text += f"\nTitle: {title}\n"
        web_text += f"Summary: {body}\n"
        web_text += f"Source: {href}\n"

    return web_text

class Question(BaseModel):
    question: str


@app.get("/")
def home():
    return {
        "message": "AI Search Robot is running!"
    }


@app.post("/ask")
def ask_question(data: Question):
    global conversation_history

    try:
        # Search the web for the current question
        web_results = search_web(data.question)

        web_context = {
            "role": "system",
            "content": f"""
You are AI Search Robot.

You have access to web search results for the user's current question.

IMPORTANT RULES:
- For current or recent information, prefer the web search results over your old training knowledge.
- Do not claim your old knowledge cutoff is the answer if newer web information is available.
- If web results contain conflicting information, say so.
- When you use web information, include the relevant source URLs in your answer.
- Answer the user's actual question clearly.

CURRENT WEB SEARCH RESULTS:

{web_results}
"""
        }

        # Save only the user's actual message in conversation memory
        conversation_history.append({
            "role": "user",
            "content": data.question
        })

        # Web results are temporary context, not permanent memory
        messages_for_ai = (
            [web_context]
            + conversation_history
        )

        response = requests.post(
    "https://api.groq.com/openai/v1/chat/completions",
    headers={
        "Authorization": f"Bearer {os.environ.get('GROQ_API_KEY')}",
        "Content-Type": "application/json"
    },
    json={
        "model": "llama-3.1-8b-instant",
        "messages": messages_for_ai,
        "temperature": 0.7
    },
    timeout=60
)
            
        

        response.raise_for_status()

        result = response.json()
        robot_answer = result["choices"][0]["message"]["content"]

        conversation_history.append({
            "role": "assistant",
            "content": robot_answer
        })

        return {
            "answer": robot_answer
        }

    except Exception as error:
        return {
            "answer": "Something went wrong: " + str(error)
        }
def new_chat():

    global conversation_history

    conversation_history = []

    return {
        "message": "Conversation memory cleared."
    }