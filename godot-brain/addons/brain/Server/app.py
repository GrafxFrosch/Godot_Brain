import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import brain


# ==============================================================================
# INITIALIZATION & CONFIGURATION
# ==============================================================================

app = FastAPI()

# Simple in-memory storage for conversation history
history = []

# CORS (Cross-Origin Resource Sharing) configuration
# This allows the Godot client (or other origins) to communicate with this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==============================================================================
# DATA MODELS (Pydantic)
# ==============================================================================





class Request(BaseModel):
    """Schema for incoming AI chat requests"""
    task: str
    image_path: str
    key: str

def debug(x):
    print(x)


# ==============================================================================
# API ENDPOINTS
# ==============================================================================

@app.get("/")
def read_root():
    """Health check endpoint to verify the server is running"""
    return {"message": "Hello!"}

@app.post("/request/")
def request(data: Request):
    """
    Main chat endpoint.
    Processes user input through the chatter module and updates history.
    """
    reply = {"reply": brain.core_brain(data.task,data.image_path, data.key)}
    # Store the exchange in the local history list

    return reply


if __name__ == "__main__":
    # Start the Uvicorn server on localhost at port 8687
    uvicorn.run(app, host="127.0.0.1", port=8687)