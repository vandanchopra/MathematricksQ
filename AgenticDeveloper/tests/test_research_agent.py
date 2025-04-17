import asyncio
import os
import json
from datetime import datetime
from AgenticDeveloper.agents.research_agent import IdeaResearcherAgent

async def main():
    # Setup
    tmp_path = "AgenticDeveloper/research_ideas"
    ideas_path = os.path.join(tmp_path, "research_ideas.json")
    os.makedirs(tmp_path, exist_ok=True)
    if not os.path.exists(ideas_path):
        with open(ideas_path, "w") as f:
            json.dump({}, f)

    agent = IdeaResearcherAgent()
    agent.ideas_dump_path = ideas_path

    print("\n=== Research Agent Test ===")
    
    # Get initial state
    with open(ideas_path, "r") as f:
        initial_ideas = json.load(f)
    initial_count = len(initial_ideas)
    initial_urls = {idea.get('source_info', {}).get('url', '') for idea in initial_ideas.values()}
    initial_urls.discard('')
    
    print(f"\nInitial state:")
    print(f"- Ideas count: {initial_count}")
    print(f"- Unique papers: {len(initial_urls)}")
    
    # Run search
    print(f"\nSearching for momentum trading ideas...")
    result = await agent.search_and_process("momentum trading", max_results=2)
    
    # Validate result format
    assert isinstance(result, dict), "Result should be a dictionary"
    assert 'new_ideas' in result, "Result missing new_ideas key"
    new_ideas = result['new_ideas']
    
    # Get final state
    with open(ideas_path, "r") as f:
        final_ideas = json.load(f)
    
    added_count = len(final_ideas) - initial_count
    
    # Print results
    print(f"\nResults:")
    print(f"- Ideas found: {len(new_ideas)}")
    print(f"- Ideas saved: {added_count}")
    
    # Validate each new idea
    if new_ideas:
        print("\nValidating ideas:")
        for idea_id, idea in new_ideas.items():
            idea_name = idea.get('idea_name', 'Unknown')
            print(f"\nIdea: {idea_name}")
            
            # Check required fields
            required_fields = ['idea_name', 'description', 'edge', 'pseudo_code', 'source_info', 'updated_dt']
            missing_fields = [f for f in required_fields if f not in idea]
            assert not missing_fields, f"Missing fields: {missing_fields}"
            
            # Validate source info
            source = idea['source_info']
            assert 'url' in source, f"Missing URL in source_info"
            assert 'title' in source, f"Missing title in source_info"
            assert source['url'] not in initial_urls, f"Duplicate paper URL"
            
            # Validate timestamp
            try:
                dt = datetime.fromisoformat(idea['updated_dt'])
                print(f"- Updated: {dt}")
            except ValueError as e:
                raise AssertionError(f"Invalid timestamp: {str(e)}")
            
            print(f"- Source: {source['title']}")
            print(f"- ID: {idea_id}")
            print("- Validation: Passed")
        
        # Verify consistency
        assert added_count == len(new_ideas), \
            f"Ideas count mismatch: {added_count} != {len(new_ideas)}"
    else:
        print("\nNo new ideas generated")
    
    print("\nTest completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())