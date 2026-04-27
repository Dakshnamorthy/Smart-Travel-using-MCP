from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys
import os

# Insert root workspace directory into the head of path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)
# CRITICAL FIX for ModuleNotFoundError:
# When executing python server/api.py, sys.path[1] gets set to the /server folder.
# This causes 'from server.tools...' to mistakenly load server/server.py instead of the folder.
# By surgically removing the local folder path, we force Python to evaluate from the root namespace!
local_dir = os.path.dirname(os.path.abspath(__file__))
if local_dir in sys.path:
    sys.path.remove(local_dir)

from server.utils.logger import get_logger
from client.client import chat

logger = get_logger(__name__)

app = FastAPI(title="Smart Travel Planner API")

# Allow React app (running on localhost:5173) to communicate with us
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For dev, allow all
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
def handle_chat(request: ChatRequest):
    logger.info({
        "event": "chat_request",
        "message": request.message
    })

    try:
        # Pass the message to our existing CLI logic and await the returned string text!
        reply = chat(request.message)
        
        # Look for the planning intent marker to enable "Save Trip" frontend buttons
        intent = "general"
        # Since we told the LLM to strip emojis/markdown, it might just print "Cost Summary" literally 
        if "Cost Summary" in reply:
            intent = "planning"

        response = {
            "reply": reply,
            "intent": intent
        }

        logger.info({
            "event": "chat_response",
            "intent": intent,
            "reply_length": len(reply)
        })

        return response
    except Exception as e:
        logger.error({
            "event": "chat_error",
            "error": str(e)
        })
        return {"reply": f"❌ Error: {str(e)}", "intent": "error"}

if __name__ == "__main__":
    import uvicorn
    # Make sure this runs on a different port from React!
    uvicorn.run(app, host="0.0.0.0", port=8000)
