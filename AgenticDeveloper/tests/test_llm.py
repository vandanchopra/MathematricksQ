import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.base import BaseAgent

class TestAgent(BaseAgent):
    async def run(self, prompt: str) -> str:
        """Simple test method to verify LLM is working"""
        response = await self.llm.ainvoke(prompt)
        return response

async def main():
    # Initialize test agent with correct config path
    agent = TestAgent("AgenticDeveloper/config/system_config.yaml")
    
    # Test prompt
    prompt = "What is the capital of France? Keep the answer very short."
    
    try:
        print("Testing LLM connection...")
        response = await agent.run(prompt)
        print(f"\nPrompt: {prompt}")
        print(f"Response: {response}")
        print("\nLLM integration is working! ✅")
    except Exception as e:
        print(f"\nError testing LLM: {str(e)} ❌")

if __name__ == "__main__":
    asyncio.run(main())