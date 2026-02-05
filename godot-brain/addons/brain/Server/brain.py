import base64
import os
from typing import TypedDict
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from numba.cuda.libdevicedecl import args
from openai import OpenAI

import app

import AzurChat

# Initialize the Azure model from the local AzurChat module

# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def ask_model(prompt: str, model: ChatOpenAI) -> str:
    """
    Queries the Azure model and returns the cleaned text response.
    """
    response = model.invoke(prompt)

    # Check if response contains a message object with a content attribute
    if hasattr(response, "content"):
        return response.content.strip()
    return str(response).strip()



# ==============================================================================
# STATE DEFINITIONS (TypedDicts)
# ==============================================================================

class InputState(TypedDict):
    """Defines the structure for input data passed to the graph."""
    task: str
    image_path: str
    model: ChatOpenAI
    client: OpenAI


class OutputState(TypedDict):
    """Defines the structure for output data produced by the graph."""
    output: TypedDict


# ==============================================================================
# GRAPH NODES
# ==============================================================================


def generate_response(state: InputState) -> dict:
    import os, base64
    from openai import OpenAI


    script_dir = os.path.dirname(__file__)
    file_path = os.path.join(script_dir, "last10", "shot.png")
    app.debug(file_path)

    client = state["client"]

    # Function to encode the image
    def encode_image(image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    # Path to your image
    image_path = file_path

    # Getting the Base64 string
    base64_image = encode_image(image_path)

    response = client.responses.create(
        model="gpt-4.1",
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": f"""
You are an NPC control unit inside a game world.

YOUR CURRENT OBJECTIVE:
{state['task']}

MOVEMENT RULES:
- You may move using direction codes only.
- Each movement code has the format: DIRECTION|PERCENTAGE
- DIRECTION must be one of:
  n = north (up)
  e = east (right)
  s = south (down)
  w = west (left)
- PERCENTAGE must be a number from 1 to 100
- The percentage represents how far across the screen you move in that direction.
- Its alway a DIRECTION cobiend with a PERCENTAGE seperated by a "|": DIRECTION|PERCENTAGE
OUTPUT FORMAT (STRICT):
- Return ONLY movement codes
- Multiple moves must be separated by commas
- NO text, NO explanations, NO formatting, NO JSON

BEHAVIOR RULES:
- Analyze the image to decide the best movement
- If no more movement is needed reply with "xx"
- Do NOT repeat the task
- Do NOT describe the image
- Do NOT add reasoning

REMEMBER:
You are a control system, not a character.
Return ONLY the movement codes.
                    """},
                    {
                        "type": "input_image",
                        "image_url": f"data:image/jpeg;base64,{base64_image}"
                    },
                ],
            }
        ],
    )
    app.debug(response.output_text)
    return {"output": response.output_text}



# ==============================================================================
# GRAPH CONSTRUCTION
# ==============================================================================

# Initialize the StateGraph with the defined state schemas
builder = StateGraph(
    state_schema=OutputState,
    input_schema=InputState,
    output_schema=OutputState
)

# Add nodes to the graph
builder.add_node("response", generate_response)

# Define the workflow edges
builder.add_edge(START, "response")
builder.add_edge("response", END)

# Compile the graph into an executable state machine
graph = builder.compile()


# ==============================================================================
# INTERFACE FUNCTIONS (Exported)
# ==============================================================================

def core_brain(prompt: str, image_path: str, key: str) -> str:
    """
    Main interface to interact with the chatter agent.
    Invokes the graph logic and returns the resulting dictionary.
    """
    model = ChatOpenAI(openai_api_key=key, model="gpt-4.1")
    client = OpenAI(api_key=key)
    result = graph.invoke({"task": prompt, "image_path": image_path, "model": model, "client": client})

    return result


# ==============================================================================
# MAIN EXECUTION (Entry Point)
# ==============================================================================

if __name__ == "__main__":
    # Script entry point for standalone testing
    pass