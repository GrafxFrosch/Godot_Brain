import base64
import os
from typing import TypedDict
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from numba.cuda.libdevicedecl import args

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


class OutputState(TypedDict):
    """Defines the structure for output data produced by the graph."""
    output: TypedDict


# ==============================================================================
# GRAPH NODES
# ==============================================================================



def generate_response(state: InputState) -> dict:
    """
    Node 1: Generates a response based on the user input and conversation history.
    """
    script_dir = os.path.dirname(__file__)  # Ordner, in dem das Skript liegt
    file_path = os.path.join(script_dir, "last10", "shot.png")
    with open(file_path, "rb") as f:
        image_base64 = base64.b64encode(f.read()).decode("utf-8")
    prompt_initial = f"""
    #YOU ARE THE CONTROL UNIT OF A NPC INSIDE A GAME#
    You get an image Input of your Game Viewport:
    {image_base64}
    You need to plan the steps to fulfill your given task:
    ###YOUR TASK###
    {state.task}
    """
    # Invoke model with user input combined with the system prompt instruction
    response = ask_model(prompt_initial, state.model)
    return {"output": response}


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
    model = ChatOpenAI(openai_api_key=key, model="gpt-4o-mini")
    result = graph.invoke({"task": prompt, "image_path": image_path, "model": model})

    return result


# ==============================================================================
# MAIN EXECUTION (Entry Point)
# ==============================================================================

if __name__ == "__main__":
    # Script entry point for standalone testing
    pass