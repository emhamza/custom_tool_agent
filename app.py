# the main agent code 
import os
import getpass
from dotenv import load_dotenv
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_google_genai import ChatGoogleGenerativeAI # New import
from langchain_core.messages import HumanMessage, ToolMessage, AIMessage
from langchain.tools import StructuredTool
from langchain_community.utilities import WikipediaAPIWrapper
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

#Helper function and Enviroment Setup

#helper funtion to set enviroment variables
def _set_env(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"{var}: ")

#load enviroment variable
load_dotenv()
_set_env("GOOGLE_API_KEY")

CREDENTIALS_FILE = 'credentials.json'

print("\nInitializing the agent components...")

#initializing the gemini modal with tool calling capabilities
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")
print("Gemini model initalized")

#Tool defination
print("Initializing tools...")

#1-Wikipedia Tool
wikipedia_wrapper  = WikipediaAPIWrapper(top_k_results=1, doc_content_chars_max=500) # type: ignore
wikipedia_tool = StructuredTool.from_function(
    func=wikipedia_wrapper.run,
    name="wikipedia",
    description="Useful for whne you need to answer questions by searching wikipedia"
)

#2-Custom Medium browsing tool
def browse_medium_article(url: str) -> str:
    """
    Fetches the main textual content of a given Medium article URL.
    This tool is designed to read and summarize specific articles.
    """

    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Attempt to find the main article content. Medium articles are often within <article> tags.
        # Fallback to common content tags or body if <article> is not found.
        main_content_tag = soup.find('article') or soup.find('main') or soup.find('section') or soup.body
        
        if main_content_tag:
            text = main_content_tag.get_text(separator=' ').strip()
            text = ' '.join(text.split()) # Normalize whitespace
        else:
            text = "Could not identify a main content area. Returning full body text."
            text = ' '.join(soup.body.get_text(separator=' ').split()) # type: ignore
        
        #return the substantial portion fo the content
        return text[:4000]
    except requests.exceptions.RequestException as e:
        return f"Error fetching url: {e}. Please ensure the url is valid and accessible"
    except Exception as e:
        return f"An unexpected error occured during browsing: {e}"
    
medium_browsing_tool = StructuredTool.from_function(
    func=browse_medium_article,
    name="medium_article_reader",
    description="Useful for when you need to read the full content of specific medium article"
)

#Goole sheet tool
def write_to_google_sheet(final_answer: str) -> str:
    """
    Writes the final human readable answer to a Google Sheet.
    Requires a 'credentials.json' file in the project root.
    named 'automation_agent' to be setup and shared with the service account.
    """

    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope) # type: ignore
        client = gspread.authorize(creds) # type: ignore

        #dedicated sheet name for agent resutls
        sheet = client.open('automation_agent').sheet1

        #append the new row to the sheet
        sheet.append_row([final_answer])
        return "Successfully saved the final answer to the google sheet."
    except Exception as e:
        return f"Error writing to google sheet: {str(e)}. Please check credentials and sheet name"
    
sheets_tool = StructuredTool.from_function(
        func=write_to_google_sheet,
        name="write_to_sheets",
        description="Useful for when you have formulated a final, human-readable answer to the user's query and need to save it. Input should be the complete final answer string."
)

#combine all the tools for llm
tools = [wikipedia_tool, medium_browsing_tool, sheets_tool]
print("All Tools ready.")

#bind the tools to the llm
llm_with_tools = llm.bind_tools(tools)

# Create a mapping from tool name to tool object for easy lookup in the tool_node
tool_map = {tool.name: tool for tool in tools}

#LangGraph States and nodes

class AgentState(TypedDict):
    """The state of the graph which holds the chat messages"""
    messages: Annotated[list, add_messages]

print("\nBuilding the langGraph workflow...")
graph_builder = StateGraph(AgentState)

def automation_chatbot(state: AgentState):
    """
    The main agent node that interacts with the llm.
    It decide whether to use the tool or provide the final answer,
    and also decide when to save the final answer to the sheet.
    """
    print("\nAgent Node: Processing message and deciding next action...")
    response = llm_with_tools.invoke(state["messages"])
    print(f"LLM generated response: {response.content[:100]} ....")
    return {"messages": [response]}

#the tool node
def tool_node(state: AgentState):
    """
    The node that execute the tool call request by the llm.
    It handles multiple tool calls and passes their results back to the llm.
    """
    print("\nThe Tool Node: Executing tool calls...")
    last_message = state["messages"][-1]

    tool_calls = last_message.tool_calls

    if not tool_calls:
        print("No tool call found in the llm's response, but routed to tool node. this is unexpected.")
        return{"messages": [AIMessage(content="No tool call to execute")]}
    
    responses = []
    for tool_call in tool_calls:
        tool_name = tool_call.get('name')
        tool_args = tool_call.get('args', {})
        tool_call_id = tool_call.get('id')

        print(f"-> Detected tool call: '{tool_name}' with args: '{tool_args}")

        if tool_name in tool_map:
            tool_to_run = tool_map[tool_name]
            try:
                #special handling for 'write_to_sheet' which excepts 'final_answer'
                if tool_name == 'write_to_sheets':
                    if 'final_answer' in tool_args:
                        tool_result = tool_to_run.invoke(tool_args['final_answer'])
                    else:
                        tool_result = "Error: 'write_to_sheets' tool called without 'final_answer' argument."
                #general handling for searcg tool that except 'query'
                elif 'query' in tool_args:
                    tool_result = tool_to_run.invoke(tool_args['query'])
                #fallback  to other tools if their arguments aren't explicitly handled
                else:
                    tool_result = tool_to_run.invoke(tool_args)
                print(f"  -> Result from '{tool_name}': {str(tool_result)[:100]}...")
                responses.append(ToolMessage(content=str(tool_result), tool_call_id=tool_call_id))
            except Exception as e:
                error_msg = f"Error executing tool '{tool_name}': {str(e)}"
                print(error_msg)
                responses.append(ToolMessage(content=error_msg, tool_call_id=tool_call_id))
        else:
            error_msg = f"Tool '{tool_name}' not found in the tool_map."
            print(f"{error_msg}")
            responses.append(ToolMessage(content=error_msg, tool_call_id=tool_call_id))
    return {"messages": responses}

#Define the conditional logic (router)
def should_continue(state: AgentState):
    """
    Determine the next step based on the last message from the agent node aka automation chatbot.
    If the llm requested a tool, route to tool_node, otherwise end the graph.
    """
    last_message = state["messages"][-1]

    if last_message.tool_calls:
        print("\nllm wants to call the tool. Routing to the 'tool_node'")
        return "call_tool"
    else:
        print("\nllm generated a final answer, routing to the 'end'")
        return "end"
    
#Graph construction

#add node to the graph
graph_builder.add_node("automation_chatbot", automation_chatbot)
graph_builder.add_node("tool_node", tool_node)

#entry point, start always goes to the  agent not or automation_chatbot
graph_builder.add_edge(START, "automation_chatbot")

#based on should continue, define the conditional edge
graph_builder.add_conditional_edges(
    "automation_chatbot",
    should_continue,
    {
        "end": END,
        "call_tool": "tool_node"
    }
)

#loop back to the automation chat bot after the tool runs
#this allows llm to synthesize the tool results or decide to call another tool (like  write_to_sheets)

graph_builder.add_edge("tool_node", "automation_chatbot")

#complie the graph
graph = graph_builder.compile()
print("Graph compiled successfully")

# --- Graph Visualization ---
print("\n📊 Generating graph visualization...")
try:
    image_bytes = graph.get_graph().draw_mermaid_png()
    image_path = "agent_workflow_graph.png"
    with open(image_path, "wb") as f:
        f.write(image_bytes)
    print(f"📊 Graph image saved to: {os.path.abspath(image_path)}")
except Exception as e:
    print(f"⚠️ Could not save graph image: {str(e)}.")

# --- Main Interaction Loop ---
print("\n" + "="*70)
print("Ready for interaction! Ask a question that requires web search or saving.")
print("Example: 'Search Wikipedia for LangChain and save the summary.'")
print("Example: 'Find a tutorial on LangChain multi-agent systems on Medium and save it.'")
print("Type 'exit' or 'quit' to end.")
print("="*70)

while True:
    try:
        user_input = input("\nYou: ")
        if user_input.lower() in ('exit', 'quit'):
            print("Goodbye")
            break

        print("\nProcessing your message...")
         # Invoke the graph with the user's input
        state = graph.invoke({"messages": [HumanMessage(content=user_input)]})

        # Get the last message from the state to display to the user
        final_response_message = state["messages"][-1]

         # Display the final human-readable response
        print("\n" + "-"*70)
        print(f"🤖 Assistant: {final_response_message.content}")
    except KeyboardInterrupt:
        print("\nExiting agent. Goodbye!")
        break
    except Exception as e:
        print(f"❌ An error occurred: {str(e)}")
        
