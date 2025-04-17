import sys
import os
from dotenv import load_dotenv
load_dotenv()
import asyncio
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import time
from agents.base import BaseAgent
from AgenticDeveloper.logger import get_logger

logger = get_logger("TestLLMAgent")

class TestAgent(BaseAgent):
    async def run(self, prompt: str) -> str:
        """Simple test method to verify LLM is working"""
        response = await self.thinking_llm.ainvoke(prompt)
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
    logger.info(f"Content length: {len(content)} chars")
    
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
    logger.info(f"Total prompt length: {len(prompt)} chars")
    
    try:
        start = time.time()
        logger.info("TEST #1 / 4 -----")
        response = await agent.run('Quick test to check if LLM is working')
        logger.info(f"Response: {response}")
        logger.info(f"Time taken 1: {time.time() - start:.2f} seconds")
        
        
        start = time.time()
        logger.info("TEST #2 / 4 -----")
        response = await agent.run('Quick test 2 to check if LLM is working')
        logger.info(f"Response: {response}")
        logger.info(f"Time taken 2: {time.time() - start:.2f} seconds")
        
        logger.info("TEST #3 / 4 -----")
        start = time.time()
        logger.info("\nFirst 100 chars of content:")
        logger.info(content[:100])
        
        logger.info("Testing LLM connection...")
        response = await agent.run(prompt)
        logger.info(f"\nPrompt: {prompt}")
        logger.info(f"Response: {response}")
        logger.info("\nLLM integration is working! ✅")
        logger.info(f"Time taken 3: {time.time() - start:.2f} seconds")
        
        
        start = time.time()
        logger.info("TEST #4 / 4 -----")
        response = await agent.run('Quick test to check if LLM is working')
        logger.info(f"Response: {response}")
        logger.info(f"Time taken 4: {time.time() - start:.2f} seconds")
        
    except Exception as e:
        logger.error(f"\nError testing LLM: {str(e)} ❌")

if __name__ == "__main__":
    asyncio.run(main())