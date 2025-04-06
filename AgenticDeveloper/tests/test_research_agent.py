import asyncio
import os
import json
from AgenticDeveloper.agents.research_agent import IdeaResearcherAgent

async def main():
    tmp_path = "AgenticDeveloper/research_ideas"
    ideas_path = os.path.join(tmp_path, "research_ideas.json")
    os.makedirs(tmp_path, exist_ok=True)
    if not os.path.exists(ideas_path):
        with open(ideas_path, "w") as f:
            json.dump({}, f)

    agent = IdeaResearcherAgent()
    agent.ideas_dump_path = ideas_path

    print(f"Running Research Agent with query 'momentum trading'...")
    await agent.search_and_process("momentum trading", max_results=2)

    with open(ideas_path, "r") as f:
        ideas = json.load(f)
    print(f"\n[Manual Test] Final saved research ideas:\n{json.dumps(ideas, indent=2)}")

if __name__ == "__main__":
    asyncio.run(main())