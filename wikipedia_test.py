#wikipedia test file code
from langchain_community.utilities import WikipediaAPIWrapper
from langchain.tools import StructuredTool

print("---Wikipedia Tool Test Script")

#define the tool
wikipedia_wrapper = WikipediaAPIWrapper(top_k_results=1, doc_content_chars_max=500) # type: ignore

#struchured tool to wikipedia wrapper
wikipedia_tool = StructuredTool.from_function(
    func=wikipedia_wrapper.run,
    name="wikipedia",
    description="Useful for when you need to answer questions by searching a Wikipedia page.",
)

#function for tool testing
def test_wikipedia_tool(query: str):
    print(f"\nCalling the wikipedia tool with query: '{query}")
    try:
        #we can invoke the tool directly just like the agent would
        result = wikipedia_tool.invoke(query)
        print("\n✅ Tool ran successfully! Here is the result:")
        print(result)
    except Exception as e:
        print(f"\n❌ An error occurred while running the Wikipedia tool: {e}")

#run the test wiht the simple query
if __name__ == "__main__":
    test_wikipedia_tool("Generative AI")