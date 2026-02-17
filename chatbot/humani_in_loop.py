
import os
from typing import Annotated, Any, Dict, Optional, TypedDict,List
from dotenv import load_dotenv
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.messages import BaseMessage, SystemMessage,HumanMessage,AIMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langgraph.graph import START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.types import interrupt,Command
from langchain_core.tools import tool
import requests
from langgraph.checkpoint.memory import MemorySaver



search_tool = DuckDuckGoSearchRun(region="us-en")

load_dotenv()
@tool
def get_news_tool(country: str):
        """Fetches the latest news headlines for a given country using the NewsData API.
        Also demonstrates the use of the `interrupt` function to ask the user if they want to see the headlines.
        """
        url = f"https://newsdata.io/api/1/latest?apikey=pub_3fa9d4888f9045a2b626e1461379a2a2&country={country}&language=en"
        response = requests.get(url)
        result = response.json()
        decision = interrupt("Do you want to see the news headlines from newsdata app? Reply with 'yes' or 'no'.")

        if decision == 'yes':
              return {
                    'status':'success',
                    'headlines':result,
                    'message':f'Here are the latest news headlines {result}'
              }
        else:
            return {
                    'status':'cancelled',
                    'message':'Okay, I will not show the news headlines.'
            }

@tool
def foreign_exchange(Quantity: int, Stock: str) -> dict:
    """
    Fetch latest foreign exchange rate for a given currency pair (e.g. 'USD', 'EUR')
    """
    url = (
        f"https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency={Quantity}&to_currency={Stock}&apikey=XMSLLLFDMNC8WV1D"
    )
    r = requests.get(url)
    result = r.json()
    

llm = ChatOpenAI(model="gpt-4o", temperature=0.7)

tools = [search_tool, get_news_tool, foreign_exchange]

llm_with_tools = llm.bind_tools(tools)

tool_node = ToolNode(tools) 
checkpointer = MemorySaver()

class state(TypedDict):
      messages : Annotated[List[BaseMessage],add_messages]

def node(states:state):
      message = states['messages']
      result = llm_with_tools.invoke(message)
      return {'messages':[result]}


graph = StateGraph(state)
graph.add_node('node',node)
graph.add_node('tools',tool_node)

graph.add_edge(START,'node')
graph.add_conditional_edges('node',tools_condition)
graph.add_edge('tools','node')


app = graph.compile(checkpointer=checkpointer)

if __name__== "__main__":
      
      thread_id = "12345"
      while True:
            user_input = input("User: ")
            if user_input.lower() == 'bye' or user_input.lower() == 'goodbye':
                  break
            
            msg = {"messages": [HumanMessage(content=user_input)]}
            result = app.invoke(msg,config = {'configurable': {'thread_id': thread_id}})

            interuppts = result.get('__interrupt__')
            if interuppts:
                  prompt_to_human = interuppts[0].value
                  print(f"HITL: {prompt_to_human}")
                  dec = input("Your decision: ").strip().lower()
            
            result = app.invoke(
            Command(resume=dec),
            config = {'configurable': {'thread_id': thread_id}}
                  )
            messages = result['messages']
            print(f"Bot: {messages[-1].content}\n")