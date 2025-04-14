import os
import json
import yaml
import asyncio
from typing import List, Dict, Optional
from tqdm.asyncio import tqdm
from AgenticDeveloper.tools.web_tools import ArxivSearchTool, PDFHandler, HTMLHandler
from AgenticDeveloper.agents.base import BaseAgent
from AgenticDeveloper.logger import get_logger
import uuid

class IdeaResearcherAgent(BaseAgent):
    def __init__(self, config_path: Optional[str] = None, config: Optional[Dict] = None):
        super().__init__(config_path, config)
        self.logger = get_logger("ResearchAgent")
        self.arxiv_tool = ArxivSearchTool()
        self.pdf_handler = PDFHandler()
        self.html_handler = HTMLHandler()
        self.ideas_dump_path = "AgenticDeveloper/research_ideas/research_ideas.json"
        os.makedirs(os.path.dirname(self.ideas_dump_path), exist_ok=True)
        if not os.path.exists(self.ideas_dump_path):
            with open(self.ideas_dump_path, "w") as f:
                json.dump({}, f)

    def _get_chunk_size_from_config(self) -> int:
        """Get the maximum words per chunk based on LLM's context window."""
        llm_config = self.config.get("llm", {})
        research_provider = llm_config.get("research_provider", "openrouter_llama4-scout")
        provider_config = llm_config.get(research_provider, {})
        context_window_k = provider_config.get("context_window_in_k", 128)
        
        # Since 1 token ≈ 0.75 words, and we want to use 50% of context window:
        # context_window_k * 1000 * 0.75 * 0.5
        max_words = int(context_window_k * 1000 * 0.75 * 0.5)
        return max_words

    def _count_words(self, text: str) -> int:
        """Count the number of words in text."""
        return len(text.split())

    def _chunk_text(self, text: str, max_words: int) -> List[str]:
        """Split text into chunks based on word count."""
        words = text.split()
        total_words = len(words)
        num_chunks = (total_words + max_words - 1) // max_words
        
        chunks = []
        for i in range(num_chunks):
            start_idx = i * max_words
            end_idx = min((i + 1) * max_words, total_words)
            chunk = ' '.join(words[start_idx:end_idx])
            chunks.append(chunk)
            
        return chunks

    async def _analyze_resource(self, text: str) -> Dict[str, dict]:
        # Get chunk size from config and create chunks
        max_words = self._get_chunk_size_from_config()
        chunks = self._chunk_text(text, max_words=max_words)
        
        ideas = {}
        
        # Process each chunk with the research LLM
        for chunk in tqdm(chunks, desc=f"Analyzing Text with LLM...", unit="chunk"):
            prompt = (
                "You are a advanced quantitative researcher in a big wallstreet trading firm, analyzing academic papers for trading strategies and indicators.\n\n"
                "Extract all tradable ideas and indicators that can provide extra edge to trading strategies.\n"
                "For each idea, provide the following information in a clear, structured format:\n\n"
                "IDEA NAME: A clear, descriptive name for the strategy/indicator\n"
                "DESCRIPTION: A detailed explanation of how the idea works. Write atleast 15 bullet points explaining the idea.\n"
                "EDGE: A thorough explanation of why this idea provides trading edge\n"
                "PSEUDOCODE: we don't want a full fledged strategy, we just want code for the idea only, \n"
                "- Signal generation logic\n"
                "- Entry/exit rules\n"
                "SOURCE: Name of the paper/source\n"
                "AUTHORS: Names of the authors\n\n"
                "Analyze the following text and extract all trading ideas:\n\n"
                f"{chunk}\n\n"
                "Format each idea as a complete, standalone trading indicator that could be implemented as part of a bigger strategy."
            )

            response = await self.call_llm(prompt, llm_destination="research")
            
            # Parse ideas from response
            idea_blocks = response.split("IDEA NAME:")[1:]  # Skip first empty split
            for block in idea_blocks:
                try:
                    lines = block.strip().split("\n")
                    
                    # Extract idea name
                    idea_name = lines[0].strip()
                    
                    # Extract other sections
                    desc_start = block.find("DESCRIPTION:") + len("DESCRIPTION:")
                    desc_end = block.find("EDGE:")
                    description = block[desc_start:desc_end].strip()
                    
                    edge_start = block.find("EDGE:") + len("EDGE:")
                    edge_end = block.find("PSEUDOCODE:")
                    edge = block[edge_start:edge_end].strip()
                    
                    pseudo_start = block.find("PSEUDOCODE:") + len("PSEUDOCODE:")
                    pseudo_end = block.find("SOURCE:")
                    pseudocode = block[pseudo_start:pseudo_end].strip()
                    
                    source_start = block.find("SOURCE:") + len("SOURCE:")
                    source_end = block.find("AUTHORS:")
                    source = block[source_start:source_end].strip()
                    
                    authors_start = block.find("AUTHORS:") + len("AUTHORS:")
                    authors = block[authors_start:].strip()
                    
                    if all([idea_name, description, edge, pseudocode, source, authors]):
                        ideas[idea_name] = {
                            'description': description,
                            'edge': edge,
                            'pseudo_code': pseudocode,
                            'source_info': {
                                'paper': source,
                                'authors': [a.strip() for a in authors.split(',')]
                            }
                        }
                    else:
                        # show me what is being rejected
                        self.logger.warning(f"Rejected idea due to missing fields: {block}")
                        continue
                        
                except Exception as e:
                    self.logger.warning(f"Failed to parse idea block: {str(e)}")
                    continue

            tqdm.write(f"Extracted {len(idea_blocks)} ideas from chunk")

        return ideas

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
                self.logger.info(f"Skipping already processed paper: {paper['title']}")
                continue

            pdf_path = await self.pdf_handler.download_pdf(paper["pdf_url"], "AgenticDeveloper/research_ideas")
            if pdf_path:
                text = self.pdf_handler.extract_text(pdf_path)
            else:
                text = ""

            # Extract multiple ideas from the paper
            ideas = await self._analyze_resource(text)

            for idea_name, idea in ideas.items():
                self._save_idea(idea_name, idea)
                
            self.logger.info(f"{len(ideas)} ideas extracted from {paper['title']}")

    def _save_idea(self, idea_name, idea):
        # Load existing ideas
        try:
            with open(self.ideas_dump_path, "r") as f:
                ideas = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            ideas = {}
        
        # Update with new idea
        idea['idea_name'] = idea_name
        ideas[str(uuid.uuid4())] = idea

        # Save updated ideas atomically
        tmp_path = self.ideas_dump_path + ".tmp"
        with open(tmp_path, "w") as f:
            json.dump(ideas, f, indent=2)
        os.replace(tmp_path, self.ideas_dump_path)

        abs_path = os.path.abspath(self.ideas_dump_path)
        self.logger.info(f"Research ideas saved at: {abs_path}")
        # self.logger.info(f"Research ideas content:\n{json.dumps(ideas, indent=2)}")