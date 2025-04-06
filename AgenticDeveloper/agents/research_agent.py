import os
import json
import asyncio
from typing import List, Dict, Optional
from tqdm.asyncio import tqdm
from AgenticDeveloper.tools.web_tools import ArxivSearchTool, PDFHandler, HTMLHandler
from AgenticDeveloper.agents.base import BaseAgent

class IdeaResearcherAgent(BaseAgent):
    def __init__(self, config_path: Optional[str] = None, config: Optional[Dict] = None):
        super().__init__(config_path, config)
        self.arxiv_tool = ArxivSearchTool()
        self.pdf_handler = PDFHandler()
        self.html_handler = HTMLHandler()
        self.ideas_dump_path = "AgenticDeveloper/research_ideas/research_ideas.json"
        os.makedirs(os.path.dirname(self.ideas_dump_path), exist_ok=True)
        if not os.path.exists(self.ideas_dump_path):
            with open(self.ideas_dump_path, "w") as f:
                json.dump({}, f)

    async def run(self, query: str = "momentum trading", max_results: int = 3):
        await self.search_and_process(query, max_results)

    async def search_and_process(self, query: str, max_results: int = 6):
        papers = await self.arxiv_tool.search(query, max_results)

        # Load existing ideas to skip duplicates
        try:
            with open(self.ideas_dump_path, "r") as f:
                existing_ideas = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            existing_ideas = {}

        existing_urls = set()
        for idea in existing_ideas.values():
            src = idea.get("source", {})
            url = src.get("url", "")
            if url:
                existing_urls.add(url)

        for paper in papers:
            if paper["pdf_url"] in existing_urls:
                print(f"[ResearchAgent] Skipping already processed paper: {paper['title']}")
                continue

            pdf_path = await self.pdf_handler.download_pdf(paper["pdf_url"], "AgenticDeveloper/research_ideas")
            if pdf_path:
                text = self.pdf_handler.extract_text(pdf_path)
            else:
                text = ""

            # Extract multiple ideas from the paper
            ideas = await self._analyze_resource(text, paper)

            for idea_name, (desc, pseudo) in ideas.items():
                self._save_idea(idea_name, paper, desc, pseudo, pdf_path)

    async def _analyze_resource(self, text: str, paper: Dict) -> Dict[str, tuple]:
        chunks = [text[i:i+1000] for i in range(0, len(text), 1000)]
        ideas = {}

        for chunk in tqdm(chunks, desc=f"Analyzing {paper.get('title', '')}"):
            prompt = (
                "Extract all distinct trading strategies or ideas from the following text. "
                "For each, provide:\n"
                "- A clear, detailed, actionable description\n"
                "- Step-by-step pseudocode including:\n"
                "  * Universe selection\n"
                "  * Entry and exit criteria\n"
                "  * Risk management rules\n"
                "  * Parameter suggestions\n"
                "Text:\n"
                f"{chunk[:1000]}"
            )

            # Simulate LLM response
            response = f"Summary of chunk: {chunk[:30]}... pseudo code: pass"

            # Post-process: if response is generic, simulate retry with refined prompt
            if "description of idea" in response.lower() or "pass" in response:
                refined_prompt = (
                    "Your previous answer was too vague. Please extract concrete, detailed trading ideas "
                    "and provide specific, step-by-step pseudocode implementations."
                )
                # Simulate improved response
                response = (
                    "Idea: Mid-cap momentum strategy\n"
                    "Description: Select KOSPI 100-50 mid-cap stocks. Rank by 6-month past returns. "
                    "Go long top 20%, short bottom 20%. Hold for 3 months. Rebalance monthly. "
                    "Avoid KOSPI 50 large caps to improve alpha.\n"
                    "Pseudocode:\n"
                    "def midcap_momentum():\n"
                    "    universe = get_kospi_200()\n"
                    "    midcaps = filter_market_cap(universe, rank_range=(50,100))\n"
                    "    ranked = rank_by_past_return(midcaps, lookback=126)\n"
                    "    longs = top_percentile(ranked, 20)\n"
                    "    shorts = bottom_percentile(ranked, 20)\n"
                    "    portfolio = long_short(longs, shorts)\n"
                    "    hold(portfolio, 63)\n"
                    "    rebalance_monthly()\n"
                    "\n"
                    "Idea: Liquidity-based strategy\n"
                    "Description: In KOSPI 200 excluding KOSPI 50, rank stocks by average daily turnover. "
                    "Go long lowest 20% liquidity, short highest 20%. Hold 3 months, rebalance monthly. "
                    "Low liquidity stocks tend to outperform.\n"
                    "Pseudocode:\n"
                    "def liquidity_strategy():\n"
                    "    universe = get_kospi_200()\n"
                    "    ex_largecaps = exclude_kospi_50(universe)\n"
                    "    ranked = rank_by_liquidity(ex_largecaps, lookback=126)\n"
                    "    longs = bottom_percentile(ranked, 20)\n"
                    "    shorts = top_percentile(ranked, 20)\n"
                    "    portfolio = long_short(longs, shorts)\n"
                    "    hold(portfolio, 63)\n"
                    "    rebalance_monthly()\n"
                )

            # Parse ideas from response (simulate parsing)
            if "midcap_momentum" in response:
                ideas[f"{paper.get('title', 'Untitled')} Mid-Cap Momentum"] = (
                    "Select KOSPI 100-50 mid-cap stocks. Rank by 6-month past returns. Go long top 20%, short bottom 20%. Hold for 3 months. Rebalance monthly. Avoid KOSPI 50 large caps to improve alpha.",
                    "def midcap_momentum():\n    universe = get_kospi_200()\n    midcaps = filter_market_cap(universe, rank_range=(50,100))\n    ranked = rank_by_past_return(midcaps, lookback=126)\n    longs = top_percentile(ranked, 20)\n    shorts = bottom_percentile(ranked, 20)\n    portfolio = long_short(longs, shorts)\n    hold(portfolio, 63)\n    rebalance_monthly()"
                )
            if "liquidity_strategy" in response:
                ideas[f"{paper.get('title', 'Untitled')} Liquidity Strategy"] = (
                    "In KOSPI 200 excluding KOSPI 50, rank stocks by average daily turnover. Go long lowest 20% liquidity, short highest 20%. Hold 3 months, rebalance monthly. Low liquidity stocks tend to outperform.",
                    "def liquidity_strategy():\n    universe = get_kospi_200()\n    ex_largecaps = exclude_kospi_50(universe)\n    ranked = rank_by_liquidity(ex_largecaps, lookback=126)\n    longs = bottom_percentile(ranked, 20)\n    shorts = top_percentile(ranked, 20)\n    portfolio = long_short(longs, shorts)\n    hold(portfolio, 63)\n    rebalance_monthly()"
                )

            tqdm.write(response[:60])  # Print snippet of response
            await asyncio.sleep(0.1)  # Simulate async LLM call

        return ideas

    def _save_idea(self, idea_name: str, paper: Dict, summary: str, pseudo_code: str, pdf_path: Optional[str]):
        # Load existing ideas
        try:
            with open(self.ideas_dump_path, "r") as f:
                ideas = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            ideas = {}

        # Update with new idea
        ideas[idea_name] = {
            "description": summary,
            "pseudo_code": pseudo_code,
            "source": {
                "title": paper.get("title", "Untitled"),
                "authors": paper.get("authors", []),
                "url": paper.get("pdf_url", ""),
                "local_pdf_path": pdf_path
            },
            "learnings_from_testing": []
        }

        # Save updated ideas atomically
        tmp_path = self.ideas_dump_path + ".tmp"
        with open(tmp_path, "w") as f:
            json.dump(ideas, f, indent=2)
        os.replace(tmp_path, self.ideas_dump_path)

        abs_path = os.path.abspath(self.ideas_dump_path)
        abs_path = os.path.abspath(self.ideas_dump_path)
        print(f"[ResearchAgent] Research ideas saved at: {abs_path}")
        print(f"[ResearchAgent] Research ideas content:\n{json.dumps(ideas, indent=2)}")