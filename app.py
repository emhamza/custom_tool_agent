
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize the Gemini model
llm = init_chat_model("google_genai:gemini-2.0-flash")

class State(TypedDict):
    # Messages have the type "list". The `add_messages` function
    # in the annotation defines how this state key should be updated
    # (in this case, it appends messages to the list, rather than overwriting them)
    messages: Annotated[list, add_messages]


graph_builder = StateGraph(State)


def custom_tool_agent(state: State):
    return {"messages": [llm.invoke(state["messages"])]}


# The first argument is the unique node name
# The second argument is the function or object that will be called whenever
# the node is used.
graph_builder.add_node("custom_tool_agent", custom_tool_agent)
graph_builder.add_edge(START, "custom_tool_agent")
graph_builder.add_edge("custom_tool_agent", END)


graph = graph_builder.compile()

# Save the graph visualization as a PNG image
try:
    image_bytes = graph.get_graph().draw_mermaid_png()
    image_path = "graph.png"
    with open(image_path, "wb") as f:
        f.write(image_bytes)
    print(f"Graph image saved to: {os.path.abspath(image_path)}")
except Exception as e:
    print("Could not save graph image:", str(e))


user_input = input("Enter a message: ")
state = graph.invoke({"messages": [{"role": "user", "content": user_input}]})

print(state["messages"][-1].content)