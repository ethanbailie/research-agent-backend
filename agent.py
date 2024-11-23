from langgraph.graph import StateGraph, END
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.checkpoint.sqlite import SqliteSaver
from typing import TypedDict, Annotated
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import operator
import json

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import uuid
from contextlib import ExitStack

load_dotenv()

model = ChatOpenAI(model="gpt-4o-mini")

search_tool = TavilySearchResults(max_results=4) 

stack = ExitStack()
memory = stack.enter_context(SqliteSaver.from_conn_string(":memory:"))

class ResearcherState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]

research_prompt = """You an expert in agentic research. \
    You are given a company's operations and you must describe cost-saving measures from utilizing AI agents. \

    If you do not have the information to accurately make a recommendation, you must perform a search to find the most relevant information. \

    Examples:
    Input: 
    User query: "Vehicle rentals in toronto, but renting out your own car" \
    Researcher context: "" \
    Output: 
    "A search is needed because I do not have any information yet regarding this idea. The search query is: 'short-termvehicle rental apps toronto'"

    Input: 
    User query: "Vehicle rentals in Toronto, but renting out your own car" \
    Researcher context: "Lyft: does not require the user to own a car. \
    Zipcar: allows users to rent cars by the day or week. \
    Turo: allows users to rent out their own cars to others. \
    Communato: has vehicles allocated over the city which users can access at any time." \
    Output: 
    "In the space of vehicle rentals in toronto, but renting out your own car, the major companies are Lyft, Zipcar, and Turo. \
    Lyft is a ridesharing service that does not require the user to own a car. \
    Zipcar is a car-sharing service that allows users to rent cars by the day or week. \
    Turo is a peer-to-peer car-sharing platform that allows individuals to rent out their own cars to others. \
    Communato is a company that has vehicles allocated over the city which users can access at any time."
    """

comparison_prompt = """You are an expert in identifying automation opportunities within a company. \
    You are given a list of company operations with oppotunity for AI automation and you must assess the cost-saving potential of each. \

    Return the a general overview of automation suggestions and the unique opportunities suggested.

    The output MUST be in the following JSON format:
    {
        "opportunities": [
            {
            "name": "Operation Name",
            "description": "Automation description",
            "unique_perspective": "why should this me automated",
            }
        ],
        "validation": {
            "automation_validity": "There are opportunities with xyz for AI agents to automate them because of abc"
        }
    }

    DO NOT return anything else.
    ANY OTHER OUTPUT WILL BE PENALIZED.
"""

class ResearchAgent:
    def __init__(self, model, tools, checkpointer, research_prompt="", comparison_prompt=""):
        self.research_prompt = research_prompt
        self.comparison_prompt = comparison_prompt
        graph = StateGraph(ResearcherState)
        graph.add_node("researcher", self.researcher)
        graph.add_node("tool_usage", self.take_action)
        graph.add_node("comparison", self.comparison)
        graph.add_conditional_edges("researcher", self.exists_action, {True: "tool_usage", False: "comparison"})
        graph.add_edge("tool_usage", "researcher")
        graph.add_edge("comparison", END)
        graph.set_entry_point("researcher")
        self.graph = graph.compile(checkpointer=checkpointer)
        self.tools = {t.name: t for t in tools}
        self.base_model = model
        self.tool_model = model.bind_tools(tools)

    def researcher(self, state: ResearcherState):
        messages = state['messages']
        if self.research_prompt:
            messages = [SystemMessage(content=self.research_prompt)] + messages
        message = self.tool_model.invoke(messages)
        return {'messages': [message]}

    def exists_action(self, state: ResearcherState):
        result = state['messages'][-1]
        return len(result.tool_calls) > 0

    def take_action(self, state: ResearcherState):
        tool_calls = state['messages'][-1].tool_calls
        results = []
        for t in tool_calls:
            print(f"Calling: {t}")
            result = self.tools[t['name']].invoke(t['args'])
            results.append(ToolMessage(tool_call_id=t['id'], name=t['name'], content=str(result)))
        print("Back to the model!")
        return {'messages': results}
    
    def comparison(self, state: ResearcherState):
        messages = state['messages']
        if self.comparison_prompt:
            messages = [SystemMessage(content=self.comparison_prompt)] + messages
        message = self.base_model.invoke(messages)
        return {'messages': [message]}

class UserInput(BaseModel):
    query: str

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins. Change to a specific domain in production for security.
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

@app.post("/research")
async def research_endpoint(user_input: UserInput):
    try:
        messages = [HumanMessage(content=user_input.query)]
        user_uuid = str(uuid.uuid4())
        
        researcher_agent = ResearchAgent(
            model, 
            [search_tool], 
            research_prompt=research_prompt, 
            comparison_prompt=comparison_prompt, 
            checkpointer=memory
        )
        
        thread = {"configurable": {"thread_id": user_uuid}}
        all_messages = []
        
        attempts = 0
        while attempts < 3:
            try:
                for event in researcher_agent.graph.stream({"messages": messages}, thread):
                    for v in event.values():
                        all_messages.extend(v['messages'])
                break
            except Exception as e:
                thread = {"configurable": {"thread_id": str(uuid.uuid4())}}
                attempts += 1
                if attempts == 3:
                    raise HTTPException(status_code=500, detail="Failed to process request after 3 attempts")
        
        return {"result": json.loads(all_messages[-1].content)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
                
