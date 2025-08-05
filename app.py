from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv
import os
import getpass 
from langchain_tavily import TavilySearch
from langchain_core.messages import HumanMessage, ToolMessage
from langchain_community.tools import ArxivQueryRun


# Helper function to set environment variables
def _set_env(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"{var}: ") 

# Load environment variables
load_dotenv()
_set_env("TAVILY_API_KEY")

print("\nInitializing components...")

# Initialize the Gemini model with tool calling capabilities
llm = init_chat_model("google_genai:gemini-2.0-flash")
print("✅ Gemini model initialized")

# Define tavily and  arxiv tool
print("Initializing tools...")
tavily_tool = TavilySearch(max_results=2)
arxiv_tool = ArxivQueryRun()

tools = [tavily_tool, arxiv_tool]
print("✅ All tool ready")

# Bind tools to the LLM. This is crucial for tool calling.
llm_with_tools = llm.bind_tools(tools)

#mapping from tool name to tool object
tool_map = {tool.name: tool for  tool in tools}

class State(TypedDict):
    messages: Annotated[list, add_messages]

print("\nBuilding the graph workflow...")
graph_builder = StateGraph(State)

#define the agent
def chatbot(state: State):
    print("\n🤖 Chatbot processing message...")
    print(f"Input messages: {state['messages']}")
    # Use the LLM with tools bound to it
    response = llm_with_tools.invoke(state["messages"])
    print(f"Generated response: {response.content}")
    return {"messages": [response]}

#tool executor funtion
def tool_node(state: State):
    print("\n🔧 Tool node: Executing search...")
    last_message = state["messages"][-1]
    
    # Get the tool calls from the LLM's response
    tool_calls = last_message.tool_calls
    
    # now there are multiple tools in the tool_calls
    if not tool_calls:
        raise ValueError("No tool calls found in the LLM's response.")
    
    responses = []
    #loop through all tool calls from the llm
    for tool_call in tool_calls:
        tool_name = tool_call['name']
        tool_args = tool_call['args']
        tool_call_id = tool_call['id']

        print(f"Tool call detected: {tool_name} wiht args: {tool_args}")

        #look up the tool from the tool_map and run it
        if tool_name in tool_map:
            tool_to_run = tool_map[tool_name]
            search_result = tool_to_run.invoke(tool_args['query'])

            print(f"Search results from: {tool_name}: {str(search_result)[:100]}")

            #return the search result as a ToolMessage to the state
            responses.append(ToolMessage(content=str(search_result), tool_call_id=tool_call_id))
        else:
            print(f" Tool '{tool_name}' not found in the tool_map.")

    return{"messages": responses}

  

# Define the conditional logic (router) - it will determine which conditional edge to go down
def should_continue(state: State):
    last_message = state["messages"][-1]
    
    # Check if the LLM's response contains tool calls
    if last_message.tool_calls:
        print("\n🤔 LLM wants to call a tool. Routing to 'tool_node'.")
        return "call_tool"
    else:
        print("\n✅ LLM generated a final answer. Routing to 'end'.")
        return "end"

# Add nodes and edges to the graph the two nodes we will cycle between
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_node("tool_node", tool_node)

# Define the entry point
graph_builder.add_edge(START, "chatbot")#this the first node that we called when input gets in

# Define the conditional edge from the chatbot
graph_builder.add_conditional_edges(
    "chatbot",
    should_continue,
    {
        "end": END,
        "call_tool": "tool_node"
    }
)

# After the tool runs, loop back to the chatbot to generate a final answer
graph_builder.add_edge("tool_node", "chatbot")#that means after the tool is called the agent node is called next

graph = graph_builder.compile()#change the graph to langchain runable
print("✅ Graph compiled successfully")

# Save the graph visualization
print("\nGenerating graph visualization...")
try:
    image_bytes = graph.get_graph().draw_mermaid_png()
    image_path = "graph_with_tools.png"
    with open(image_path, "wb") as f:
        f.write(image_bytes)
    print(f"📊 Graph image saved to: {os.path.abspath(image_path)}")
except Exception as e:
    print("⚠️ Could not save graph image:", str(e))

# Main interaction loop
print("\n" + "="*50)
print("Ready for interaction! (Press Ctrl+C to exit)")
print("="*50)

while True:
    try:
        user_input = input("\nYou: ")
        if user_input.lower() in ('exit', 'quit'):
            break
            
        print("\nProcessing your message...")
        # Use invoke to run the graph and get the final state
        state = graph.invoke({"messages": [HumanMessage(content=user_input)]})
        response = state["messages"][-1].content
        
        print("\n" + "-"*50)
        print(f"🤖 Assistant: {response}")
        print("-"*50)
        
    except KeyboardInterrupt:
        print("\nExiting...")
        break
    except Exception as e:
        print(f"⚠️ An error occurred: {str(e)}")
