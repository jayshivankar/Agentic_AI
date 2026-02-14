from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool, BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient
from dotenv import load_dotenv
import aiosqlite
import requests
import asyncio
import threading


load_dotenv()

# Dedicated async loop for backend tasks
_ASYNC_LOOP = asyncio.new_event_loop()
_ASYNC_THREAD = threading.Thread(target=_ASYNC_LOOP.run_forever, daemon=True)
_ASYNC_THREAD.start()


def _submit_async(coro):
    return asyncio.run_coroutine_threadsafe(coro, _ASYNC_LOOP)


def run_async(coro):
    return _submit_async(coro).result()


def submit_async_task(coro):
    """Schedule a coroutine on the backend event loop."""
    return _submit_async(coro)


client = MultiServerMCPClient({
    "tools_content":
    {
        "transport": "stdio",
        "command": "python3",
        "args" : ["/home/jay/Agentic_AI/chatbot/tools_mcp.py"]
    }

})

def get_tools():
    try:
        return client.get_tools()
    except Exception as e:
        return []

search_tool = DuckDuckGoSearchRun(region="us-en")


tools = [search_tool,*get_tools]

llm = ChatOpenAI()
llm_tools = llm.bind_tools(tools=tools)

class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    
async def chat_node(state: ChatState):
    messages = state['messages']
    response = await llm_tools.invoke(messages)
    return {"messages": [response]}
    
async def _init_checkpointer():
    conn = await aiosqlite.connect(database='chatbot.db', check_same_thread=False)
    return AsyncSqliteSaver(conn=conn)
    
checkpointer = run_async(_init_checkpointer())

toolnode = ToolNode(tools)

graph = StateGraph(ChatState)
graph.add_node("chat_node", chat_node)
graph.add_node("tools",toolnode)

graph.add_edge(START, "chat_node")
graph.add_conditional_edges("chat_node",tools_condition)
graph.add_edge("tools","chat_node")

chatbot = graph.compile(checkpointer=checkpointer)



async def _alist_threads():
    all_threads = set()
    async for checkpoint in checkpointer.alist(None):
        all_threads.add(checkpoint.config["configurable"]["thread_id"])
    return list(all_threads)


def retrieve_all_threads():
    return run_async(_alist_threads())