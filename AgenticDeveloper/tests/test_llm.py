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
    
    # Create large test content
    content = """
    Pairs trading is a market neutral trading strategy enabling traders to profit from virtually any market conditions: uptrend, downtrend, or sideways movement. This trading strategy is categorized as a statistical arbitrage and convergence trading strategy.

    The strategy monitors performance of two historically correlated securities. When the correlation between the two securities temporarily weakens, i.e. one stock moves up while the other moves down, the pairs trade would be to short the outperforming stock and to long the underperforming one, betting that the "spread" between the two would eventually converge.
    """ * 200  # Repeat to make it large
    
    content = content[:60000]  # Limit to 60k chars
    print(f"Content length: {len(content)} chars")
    
    prompt = f"""Analyze this trading strategy content and extract key points:

Content:
{content}

Return in JSON format:
{{
    "summary": "Brief summary of pairs trading",
    "key_points": ["Main points about the strategy"],
    "implementation": ["Implementation details"]
}}
"""
    print(f"Total prompt length: {len(prompt)} chars")
    
    try:
        print("\nFirst 100 chars of content:")
        print(content[:100])
        
        print("Testing LLM connection...")
        response = await agent.run(prompt)
        print(f"\nPrompt: {prompt}")
        print(f"Response: {response}")
        print("\nLLM integration is working! ✅")
    except Exception as e:
        print(f"\nError testing LLM: {str(e)} ❌")

if __name__ == "__main__":
    asyncio.run(main())