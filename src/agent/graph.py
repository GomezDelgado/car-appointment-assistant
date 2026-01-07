"""LangGraph agent for car dealership appointments."""

from typing import Annotated, TypedDict
from langchain_groq import ChatGroq
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from src.mcp.tools import TOOLS


class AgentState(TypedDict):
    """State for the appointment assistant agent."""
    messages: Annotated[list[BaseMessage], add_messages]


SYSTEM_PROMPT = """You are a car dealership appointment assistant. You MUST use the tools provided.

WHEN TO USE EACH TOOL:
- User asks about contact info, phone, address, details of a dealership → use get_dealership_info
- User asks about dealerships or locations → use search_dealerships
- User asks about availability WITHOUT wanting to book → use check_availability
- User wants the SOONEST/EARLIEST/NEXT AVAILABLE appointment → use book_next_available
- User wants to book a SPECIFIC date and time → use book_appointment
- User asks about their bookings/reservations/appointments → use get_my_bookings
- User wants to CANCEL a booking → use cancel_my_booking
- User wants to MODIFY/CHANGE/RESCHEDULE a booking → use modify_my_booking

BOOKING RULES:
- "sooner possible", "earliest", "next available", "as soon as possible" → use book_next_available
- Specific date AND time provided → use book_appointment
- Always use dealership NAMES (e.g., "Downtown Auto Service"), never IDs
- If dealership not specified, use "Downtown Auto Service"
- For cancel/modify, first call get_my_bookings to show the user their bookings and get the booking ID

Available services: oil_change, tire_rotation, brake_inspection, general_review, state_inspection, air_conditioning, battery_check.
"""


def create_agent(model_name: str = "llama-3.3-70b-versatile"):
    """Create and return the appointment assistant agent graph."""
    
    llm = ChatGroq(model=model_name, temperature=0)
    llm_with_tools = llm.bind_tools(TOOLS)
    llm_no_tools = ChatGroq(model=model_name, temperature=0)
    
    def call_model(state: AgentState) -> dict:
        """Call the LLM - with tools only if no tool has been called yet."""
        messages = state["messages"]
        
        has_tool_result = any(
            msg.type == "tool" for msg in messages
        )
        
        full_messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(messages)
        
        if has_tool_result:
            response = llm_no_tools.invoke(full_messages)
        else:
            response = llm_with_tools.invoke(full_messages)
        
        return {"messages": [response]}
    
    def should_continue(state: AgentState) -> str:
        """Determine if we should continue to tools or end."""
        last_message = state["messages"][-1]
        
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        
        return END
    
    graph_builder = StateGraph(AgentState)
    graph_builder.add_node("agent", call_model)
    graph_builder.add_node("tools", ToolNode(TOOLS))
    
    graph_builder.add_edge(START, "agent")
    graph_builder.add_conditional_edges("agent", should_continue, ["tools", END])
    graph_builder.add_edge("tools", "agent")
    
    return graph_builder.compile()


agent = create_agent()


def _extract_tool_results(messages: list[BaseMessage]) -> str:
    """Extract the last tool result from messages."""
    for msg in reversed(messages):
        if msg.type == "tool" and msg.content:
            return msg.content
    return ""


async def chat(message: str, history: list[BaseMessage] | None = None) -> str:
    """Send a message to the agent and get a response."""
    messages = history or []
    messages.append(HumanMessage(content=message))

    result = await agent.ainvoke({"messages": messages})
    all_messages = result["messages"]
    last_message = all_messages[-1]

    # If tools were used, return only tool data (avoid duplication)
    tool_data = _extract_tool_results(all_messages)
    if tool_data:
        return tool_data

    return last_message.content


def chat_sync(message: str, history: list[BaseMessage] | None = None) -> str:
    """Synchronous version of chat."""
    messages = history or []
    messages.append(HumanMessage(content=message))

    result = agent.invoke({"messages": messages})
    all_messages = result["messages"]
    last_message = all_messages[-1]

    # If tools were used, return only tool data (avoid duplication)
    tool_data = _extract_tool_results(all_messages)
    if tool_data:
        return tool_data

    return last_message.content
