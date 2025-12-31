"""Debug script to see agent decisions step by step."""

from dotenv import load_dotenv
load_dotenv()

from langchain_core.messages import HumanMessage
from src.agent.graph import agent

def debug_conversation(message: str):
    """Run agent and show each step."""
    
    print("=" * 60)
    print(f"USER: {message}")
    print("=" * 60)
    
    messages = [HumanMessage(content=message)]
    step = 0
    
    # Stream through each step of the graph
    for event in agent.stream({"messages": messages}):
        step += 1
        print(f"\n--- Step {step} ---")
        
        for node_name, node_output in event.items():
            print(f"Node: {node_name}")
            
            if "messages" in node_output:
                for msg in node_output["messages"]:
                    msg_type = type(msg).__name__
                    
                    # Check if it's a tool call
                    if hasattr(msg, "tool_calls") and msg.tool_calls:
                        print(f"  [{msg_type}] LLM wants to call tools:")
                        for tc in msg.tool_calls:
                            print(f"    -> {tc['name']}({tc['args']})")
                    
                    # Check if it's a tool response
                    elif msg_type == "ToolMessage":
                        content = msg.content[:200] + "..." if len(msg.content) > 200 else msg.content
                        print(f"  [{msg_type}] Tool result:")
                        print(f"    {content}")
                    
                    # Regular AI message (final response)
                    else:
                        content = msg.content[:300] + "..." if len(msg.content) > 300 else msg.content
                        print(f"  [{msg_type}] {content}")
    
    print("\n" + "=" * 60)
    print("END OF CONVERSATION")
    print("=" * 60)


if __name__ == "__main__":
    # Test query
    debug_conversation("I need an oil change in Madrid, what's available?")
