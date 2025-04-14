import asyncio
import os
import json
from AgenticDeveloper.agents.research_agent import IdeaResearcherAgent
from AgenticDeveloper.tools.web_tools import PDFHandler

async def test_idea_extraction(input_path: str):
    """
    Test the idea extraction functionality with a PDF file.

    Args:
        input_path: str - Path to PDF file
    """
    # Instantiate the agent
    agent = IdeaResearcherAgent()
    # Extract text from the PDF
    text = agent.pdf_handler.extract_text(input_path)
    # Prepare a dummy paper dict (minimal required fields)
    # Analyze the resource to extract ideas
    ideas = await agent._analyze_resource(text)
    # Print the extracted ideas for inspection
    print(json.dumps(ideas, indent=2))
    for idea_name, idea in ideas.items():
        agent._save_idea(idea_name, idea)
    
async def main():
    test_input = "AgenticDeveloper/research_papers/2302.10175v1.pdf"
    await test_idea_extraction(test_input)

if __name__ == "__main__":
    asyncio.run(main())