import os
import asyncio
from typing import List, Dict
from mcp.server.fastmcp import FastMCP
from brave_search_python_client import BraveSearch, WebSearchRequest
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv('.env')

# Get API key from environment
api_key = os.getenv('BRAVE_SEARCH_PYTHON_CLIENT_API_KEY')
if not api_key:
    raise ValueError("Brave API key not found")

mcp = FastMCP("brave_search")

print("Brave Search Server initializing...")

@mcp.tool()
async def search_related_articles(query: str, max_results: int = 5) -> List[Dict]:
    """
    Search for related articles using Brave Search API.
    
    Args:
        query: The search query
        max_results: Maximum number of results to retrieve (default: 5)
        
    Returns:
        List of dictionaries containing related article information
    """
    # Initialize Brave Search client with API key
    brave = BraveSearch(api_key=api_key)
    
    try:
        # Perform the search using WebSearchRequest (await the coroutine)
        response = await brave.web(WebSearchRequest(q=query, count=max_results))
        
        # Format the results - According to the API docs, web search results are in response.web.results
        related_articles = []
        
        if hasattr(response, 'web') and hasattr(response.web, 'results'):
            for result in response.web.results:
                article = {
                    'title': getattr(result, 'title', ''),
                    'url': getattr(result, 'url', ''),
                    'description': getattr(result, 'description', ''),
                    'page_age': getattr(result, 'page_age', ''),
                    'page_fetched': getattr(result, 'page_fetched', ''),
                    'is_source_local': getattr(result, 'is_source_local', False),
                    'family_friendly': getattr(result, 'family_friendly', True)
                }
                related_articles.append(article)
        else:
            return [{"error": "No web search results found in response"}]
        
        return related_articles
    
    except Exception as e:
        return [{"error": f"Error searching for related articles: {str(e)}"}]

if __name__ == "__main__":
    print("Starting Brave Search MCP server...")
    try:
        mcp.run(transport='stdio')
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Server error: {str(e)}")
    finally:
        print("Server shutdown complete")