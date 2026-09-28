import json 
import math 

# tool implementation (the actual python code for the tool) goes here

def calculator(expression: str) -> dict:
    """
    Safely evaluate a basic arithmetic expression 
    """
    allowed_name = {"sqrt":math.sqrt, "pow":math.pow, "abs":abs, "round":round}
    try:
        # Evaluate the expression using eval in a restricted environment
        result = eval(expression, {"__builtins__": None}, allowed_name)
        return {"result": result}
    
    except Exception as e:
        return {"error": f"Error evaluating expression: {str(e)}"}
    
def web_search(query: str) -> dict:
    """
    Placeholder web search tool.Replace with a real API (eg. SerpAPI, Bing Search API) for production use.
    Kept as a stub so the tool calling loop works wihtuout extra signups 
    """
    return {
        "results":[
            {"title":f"Stub result for '{query}'", "url":"https://example.com", "snippet":"This is a stub search result. Replace with a real search API."}
        ]
    }
    
def query_knowledge_base(query: str) -> dict:
    """Retrieves relevant chunks from the vector store for the given query."""
    from app.rag.retriever import retrieve

    chunks = retrieve(query, top_k=4)
    if not chunks:
        return {"chunks": [], "note": "No relevant information found in knowledge base."}

    return {
        "chunks": [
            {"document": c["metadata"]["source"], "chunk_id": c["chunk_id"], "text": c["text"]}
            for c in chunks
        ]
    }

from datetime import datetime, timezone


def get_current_time() -> dict:
    """Returns the current date and time in UTC."""
    now = datetime.now(timezone.utc)
    return {
        "iso": now.isoformat(),
        "utc_time": now.strftime("%Y-%m-%d %H:%M:%S UTC"),
    }


# tool schemas (what we tell the model is available, and how to call it)

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "Evaluate a basic arithmetic expression. Allowed functions: sqrt, pow, abs, round. Example: 'sqrt(16) + pow(2,3)'",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "The arithmetic expression to evaluate.",
                    }
                },
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_knowledge_base",
            "description": "Search the internal document knowledge base for information relevant to the user's query. Returns a list of document chunks that may contain the answer.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The user's query to search for in the knowledge base.",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for up-to-date public information, news, and external facts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query string.",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Get the current real-world UTC timestamp and date.",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
]

TOOL_FUNCTIONS = {
    "calculator": calculator,
    "query_knowledge_base": query_knowledge_base,
    "web_search": web_search,
    "get_current_time": get_current_time,
}

def execute_tool(name: str, arguments_json: str) -> str:
    """Execute a tool by name and return a JSON string result."""
    if name not in TOOL_FUNCTIONS:
        return json.dumps({"error": f"Tool '{name}' not found"})

    try:
        args = json.loads(arguments_json) if arguments_json else {}
    except json.JSONDecodeError as e:
        return json.dumps({"error": f"Invalid JSON arguments: {str(e)}"})

    try:
        result = TOOL_FUNCTIONS[name](**args)
        return json.dumps(result)
    except Exception as e:
        return json.dumps({"error": f"Tool execution failed: {str(e)}"})
