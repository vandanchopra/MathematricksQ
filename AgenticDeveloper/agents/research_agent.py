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
import datetime as dt

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
                "You are an advanced quantitative researcher in a major Wall Street trading firm, analyzing academic papers for trading strategies and indicators.\n\n"
                "Extract all tradable ideas and indicators that can provide extra edge to trading strategies. Format EACH idea as a JSON object with the following structure:\n\n"
                "{\n"
                '  "idea_name": "Clear strategy name",\n'
                '  "description": [\n'
                '    "Point 1 about how it works",\n'
                '    "Point 2 about how it works",\n'
                '    "... at least 15 detailed bullet points"\n'
                '  ],\n'
                '  "edge": [\n'
                '    "Point 1 about trading edge",\n'
                '    "Point 2 about trading edge",\n'
                '    "... multiple points about why this provides edge"\n'
                '  ],\n'
                '  "pseudo_code": {\n'
                '    "signal_generation": "Detailed signal generation logic",\n'
                '    "entry_rules": "Clear entry conditions",\n'
                '    "exit_rules": "Clear exit conditions"\n'
                '  }\n'
                "}\n\n"
                "Analyze this text and extract all trading ideas:\n\n"
                f"{chunk}\n\n"
                "IMPORTANT:\n"
                "1. Return a JSON array of ideas, each following the exact structure above\n"
                "2. Include at least 15 points in description\n"
                "3. Provide specific signal generation and trading rules\n"
                "4. Ensure the JSON is properly formatted and valid"
            )

            response = await self.call_llm(prompt, llm_destination="research")
            
            # Log response for debugging
            self.logger.info(f"LLM Response:\n{response}")
            
            # Parse JSON from response
            chunk_ideas = {}
            try:
                self.logger.debug("Looking for JSON array in response")
                # Find JSON array in response, handle code blocks
                json_start = response.find("```json")
                if json_start != -1:
                    json_start = response.find("[", json_start)
                    json_end = response.find("```", json_start)
                else:
                    json_start = response.find("[")
                    json_end = response.rfind("]") + 1

                if json_start == -1 or json_end == 0:
                    self.logger.warning("No JSON array found in response")
                    continue
                
                # Parse JSON array
                json_str = response[json_start:json_end]
                try:
                    paper_ideas = json.loads(json_str)
                except json.JSONDecodeError as e:
                    # Try cleaning up the JSON
                    json_str = json_str.replace('}\n  }', '}}')  # Fix common formatting issue
                    paper_ideas = json.loads(json_str)
                
                if not paper_ideas:
                    self.logger.warning("Empty JSON array in response")
                    continue
                
                self.logger.info(f"Found {len(paper_ideas)} potential ideas in response")
                
                # Process each idea
                successful_ideas = 0
                for idea_json in paper_ideas:
                    # Extract and validate idea name
                    idea_name = idea_json.get('idea_name')
                    if not idea_name:
                        self.logger.warning("Idea missing name, skipping")
                        continue
                    
                    # Validate required fields
                    required_fields = ['description', 'edge', 'pseudo_code']
                    if not all(k in idea_json for k in required_fields):
                        missing = [k for k in required_fields if k not in idea_json]
                        self.logger.warning(f"Idea '{idea_name}' missing fields: {missing}")
                        continue
                    
                    # Add to ideas dict with our internal format
                    chunk_ideas[idea_name] = {
                        'description': '\n'.join(idea_json['description']),
                        'edge': '\n'.join(idea_json['edge']),
                        'pseudo_code': idea_json['pseudo_code'],
                        'source_info': {}  # Will be added by caller
                    }
                    successful_ideas += 1
                    self.logger.info(f"Successfully parsed idea: {idea_name}")
                
                if successful_ideas > 0:
                    tqdm.write(f"Extracted {successful_ideas} ideas from chunk")
                    ideas.update(chunk_ideas)
                
            except json.JSONDecodeError as e:
                self.logger.warning(f"Failed to parse JSON response: {str(e)}")
                self.logger.warning(f"Failed to parse JSON, raw content: {json_str[:200]}...")
                continue
            except Exception as e:
                self.logger.warning(f"Error processing ideas: {str(e)}")
                continue

            if chunk_ideas:
                tqdm.write(f"Extracted {len(ideas)} ideas from chunk")

        return ideas

    async def run(self, query: str = "momentum trading", max_results: int = 3):
        await self.search_and_process(query, max_results)

    async def search_and_process(self, query: str, max_results: int = 6) -> Dict[str, Dict]:
        papers = await self.arxiv_tool.search(query, max_results)

        # Load existing ideas to skip duplicates
        try:
            with open(self.ideas_dump_path, "r") as f:
                existing_ideas = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            existing_ideas = {}

        # Track processed URLs using stored URLs in ideas
        processed_urls = {
            idea.get('source_info', {}).get('url', '')
            for idea in existing_ideas.values()
        }
        processed_urls.discard('')  # Remove empty URLs
        
        new_ideas = {}
        for paper in papers:
            if paper["pdf_url"] in processed_urls:
                self.logger.info(f"Skipping already processed paper: {paper['title']}")
                continue

            pdf_path = await self.pdf_handler.download_pdf(paper["pdf_url"], "AgenticDeveloper/research_ideas")
            if pdf_path:
                text = self.pdf_handler.extract_text(pdf_path)
            else:
                text = ""

            # Extract multiple ideas from the paper
            paper_ideas = await self._analyze_resource(text)
            
            # Add source info and save each idea
            for idea_name, idea in paper_ideas.items():
                try:
                    # Update source info
                    idea['source_info'].update({
                        'url': paper["pdf_url"],
                        'title': paper["title"]
                    })
                    
                    # Save idea and get ID
                    idea_id = self._save_idea(idea_name, idea)
                    if idea_id:
                        new_ideas[idea_id] = idea.copy()  # Store copy of saved idea
                    else:
                        self.logger.warning(f"Failed to save idea: {idea_name} - no ID returned")
                except Exception as e:
                    self.logger.error(f"Error saving idea {idea_name}: {str(e)}")
                    continue

        self.logger.info(f"Total ideas added in this run: {len(new_ideas)}")
        if new_ideas:
            self.logger.info("New ideas generated:")
            for idea_id, idea in new_ideas.items():
                self.logger.info(f"  - {idea['idea_name']} (ID: {idea_id})")
                
        return {'new_ideas': new_ideas}

    def _save_idea(self, idea_name, idea) -> str:
        # Load existing ideas
        try:
            with open(self.ideas_dump_path, "r") as f:
                ideas = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            ideas = {}
        
        # Update with new idea
        idea['idea_name'] = idea_name
        idea['updated_dt'] = dt.datetime.now().isoformat()
        idea_id = str(uuid.uuid4())
        ideas[idea_id] = idea.copy()  # Make a copy to avoid reference issues
        
        # Save updated ideas atomically
        tmp_path = self.ideas_dump_path + ".tmp"
        with open(tmp_path, "w") as f:
            json.dump(ideas, f, indent=2)
        os.replace(tmp_path, self.ideas_dump_path)

        abs_path = os.path.abspath(self.ideas_dump_path)
        self.logger.info(f"Research ideas saved at: {abs_path}")
        # self.logger.info(f"Research ideas content:\n{json.dumps(ideas, indent=2)}")
        
        return idea_id