import arxiv
import json
import os
from typing import List
from mcp.server.fastmcp import FastMCP
from mcp.client import MCPClient



PAPER_DIR = "papers"

mcp = FastMCP("research")
brave_client = MCPClient("brave_search")

print("Server initializing...")

@mcp.tool()
def search_papers(topic: str, max_results: int = 5) -> List[str]:
    """
    Search for papers on arXiv based on a topic and store their information.
    
    Args:
        topic: The topic to search for
        max_results: Maximum number of results to retrieve (default: 5)
        
    Returns:
        List of paper IDs found in the search
    """
    print(f"Searching for papers on topic: {topic}")
     
    client = arxiv.Client()

    search = arxiv.Search(
        query = topic,
        max_results = max_results,
        sort_by = arxiv.SortCriterion.Relevance
    )

    papers = client.results(search)
    path = os.path.join(PAPER_DIR, topic.lower().replace(" ", "_"))
    os.makedirs(path, exist_ok=True)
    
    file_path = os.path.join(path, "papers_info.json")

    try:
        with open(file_path, "r") as json_file:
            papers_info = json.load(json_file)
    except (FileNotFoundError, json.JSONDecodeError):
        papers_info = {}

    # Process each paper and add to papers_info  
    paper_ids = []
    for paper in papers:
        paper_ids.append(paper.get_short_id())
        paper_info = {
            'title': paper.title,
            'authors': [author.name for author in paper.authors],
            'summary': paper.summary,
            'pdf_url': paper.pdf_url,
            'published': str(paper.published.date())
        }
        papers_info[paper.get_short_id()] = paper_info
    
    # Save updated papers_info to json file
    with open(file_path, "w") as json_file:
        json.dump(papers_info, json_file, indent=2)
    
    print(f"Results are saved in: {file_path}")
    
    return paper_ids

@mcp.tool()
def extract_info(paper_id: str) -> str:
    """
    Search for information about a specific paper across all topic directories.
    
    Args:
        paper_id: The ID of the paper to look for
        
    Returns:
        JSON string with paper information if found, error message if not found
    """
    print(f"Extracting info for paper: {paper_id}")
 
    for item in os.listdir(PAPER_DIR):
        item_path = os.path.join(PAPER_DIR, item)
        if os.path.isdir(item_path):
            file_path = os.path.join(item_path, "papers_info.json")
            if os.path.isfile(file_path):
                try:
                    with open(file_path, "r") as json_file:
                        papers_info = json.load(json_file)
                        if paper_id in papers_info:
                            return json.dumps(papers_info[paper_id], indent=2)
                except (FileNotFoundError, json.JSONDecodeError) as e:
                    print(f"Error reading {file_path}: {str(e)}")
                    continue
    
    return f"There's no saved information related to paper {paper_id}."

# @mcp.tool()
# def summarize_paper(paper_id: str) -> str:
#     """
#     Summarize a paper based on its ID.
    
#     Args:
#         paper_id: The ID of the paper to summarize
        
#     Returns:
#         A summary of the paper
#     """

#     # Load the paper information
#     path = os.path.join(PAPER_DIR, paper_id.lower().replace(" ", "_"))
#     file_path = os.path.join(path, "papers_info.json")
    
#     try:
#         with open(file_path, "r") as json_file:
#             papers_info = json.load(json_file)
#     except (FileNotFoundError, json.JSONDecodeError):
#         return f"No information found for paper {paper_id}."
    
#     # Get the paper information
#     paper_info = papers_info.get(paper_id, None)
    

@mcp.tool()
def find_related_articles(paper_id: str, max_results: int = 5) -> List[dict]:
    """
    Search for related articles using Brave Search API based on a paper's title and authors.
    
    Args:
        paper_id: The ID of the paper to find related articles for
        max_results: Maximum number of results to retrieve (default: 5)
        
    Returns:
        List of dictionaries containing related article information
    """
    # First get the paper information
    for item in os.listdir(PAPER_DIR):
        item_path = os.path.join(PAPER_DIR, item)
        if os.path.isdir(item_path):
            file_path = os.path.join(item_path, "papers_info.json")
            if os.path.isfile(file_path):
                try:
                    with open(file_path, "r") as json_file:
                        papers_info = json.load(json_file)
                        if paper_id in papers_info:
                            paper_info = papers_info[paper_id]
                            break
                except (FileNotFoundError, json.JSONDecodeError) as e:
                    print(f"Error reading {file_path}: {str(e)}")
                    continue
    else:
        return [{"error": f"No information found for paper {paper_id}"}]
    
    # Create search query using paper title and authors
    search_query = f"{paper_info['title']} {' '.join(paper_info['authors'])}"
    
    try:
        # Use the Brave search client to perform the search
        related_articles = brave_client.search_related_articles(query=search_query, max_results=max_results)
        return related_articles
    
    except Exception as e:
        return [{"error": f"Error searching for related articles: {str(e)}"}]

if __name__ == "__main__":
    print("Starting MCP server...")
    try:
        mcp.run(transport='stdio')
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Server error: {str(e)}")
    finally:
        print("Server shutdown complete")

