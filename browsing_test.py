# test code for medium search tool

import requests
from bs4 import BeautifulSoup
from langchain.tools import StructuredTool
from urllib.parse import quote_plus # Import for URL encoding

print("--- Browsing Tool Test Script (Medium Search) ---")

def browse_url(url: str) -> str:
    """
    Fetches the content of a given URL and returns the text.
    This is a simplified version of a browsing tool.
    """
    try:
        # Send the HTTP GET request to the URL
        response = requests.get(url, timeout=10)
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)

        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract all <a> (anchor) tags
        # We'll collect both the link text and its href attribute
        links_info = []
        for link_tag in soup.find_all('a', href=True): # Only get <a> tags with an href attribute
            text = link_tag.get_text(separator=' ').strip()
            href = link_tag['href'] # type: ignore # Get the href attribute
            if text: # Only include links that have visible text
                links_info.append(f"Text: '{text}' | URL: '{href}'")
        
        # Join the extracted link information into a single string
        # Limit the total output for a concise test
        result_text = "\n".join(links_info)
        return result_text[:2000] # Return the first 2000 characters for a short tes
        return text[:1000] # Return the first 1000 characters for a short test
    
    except requests.exceptions.RequestException as e:
        return f"Error fetching URL: {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"

# Wrap the function in the structured tool
browsing_tool = StructuredTool.from_function(
    func=browse_url,
    name="medium_search_tool", # Renamed for clarity for Medium search
    description="Useful for when you need to search for articles on Medium.com."
)

# Define the function to test the tool with a query
def test_medium_search_tool(query: str):
    print(f"\nCalling the Medium search tool with query: '{query}'")
    
    # Construct the Medium search URL
    # Use quote_plus to properly encode the query for a URL
    search_url = f"https://medium.com/search?q={quote_plus(query)}"
    print(f"Constructed Medium Search URL: {search_url}")

    try:
        # 'invoke' the tool directly with the constructed URL
        result = browsing_tool.invoke(search_url)
        print("\n✅ Tool ran successfully! Here is the beginning of the search results content:")
        print(result)
    except Exception as e:
        print(f"\n❌ An error occurred while running the Medium search tool: {e}")

# Run the test with a sample search query.
if __name__ == "__main__":
    test_medium_search_tool("LangChain agent tutorial")

