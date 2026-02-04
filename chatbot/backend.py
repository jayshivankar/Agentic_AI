from langgraph.graph import StateGraph,START,END
from typing import TypedDict,Annotated
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages




load_dotenv()

model = ChatOpenAI(model_name="gpt-4", temperature=0.6)

class states(TypedDict):
    messages:Annotated[list[BaseMessage], add_messages]

def llm_response(state:states):
    messages = state['messages']
    response = model.invoke(messages)
    return {'messages': [response]}

checkpointer = InMemorySaver()

graph = StateGraph(states)
graph.add_node('llm response',llm_response)
graph.add_edge(START,'llm response')
graph.add_edge('llm response',END)

chatbot = graph.compile(checkpointer=checkpointer)
