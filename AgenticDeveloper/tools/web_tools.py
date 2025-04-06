import aiohttp
import asyncio
import os
import tempfile
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import fitz  # PyMuPDF
import arxiv

class ArxivSearchTool:
    """Tool for searching arXiv and retrieving paper metadata and PDF URLs."""

    async def search(self, query: str, max_results: int = 5) -> List[Dict]:
        results = []
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance
        )
        client = arxiv.Client()
        loop = asyncio.get_event_loop()
        papers = await loop.run_in_executor(None, lambda: list(client.results(search)))
        for paper in papers:
            results.append({
                "title": paper.title,
                "authors": [author.name for author in paper.authors],
                "summary": paper.summary,
                "pdf_url": paper.pdf_url,
                "entry_id": paper.entry_id
            })
        return results

class PDFHandler:
    """Tool for downloading PDFs and extracting their text."""

    async def download_pdf(self, url: str, save_dir: str) -> Optional[str]:
        # Override save_dir to always use research_papers folder
        save_dir = "AgenticDeveloper/research_papers"
        os.makedirs(save_dir, exist_ok=True)

        filename_base = url.split("/")[-1]
        if not filename_base.endswith(".pdf"):
            filename_base += ".pdf"
        save_path = os.path.join(save_dir, filename_base)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        with open(save_path, "wb") as f:
                            f.write(await resp.read())
                        return save_path
        except Exception as e:
            print(f"Error downloading PDF: {e}")
        return None

    def extract_text(self, file_path: str) -> str:
        text = ""
        try:
            doc = fitz.open(file_path)
            for page in doc:
                text += page.get_text()
        except Exception as e:
            print(f"Error extracting PDF text: {e}")
        return text

class HTMLHandler:
    """Tool for downloading HTML pages and extracting their text."""

    async def download_html(self, url: str) -> Optional[str]:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        return await resp.text()
        except Exception as e:
            print(f"Error downloading HTML: {e}")
        return None

    def extract_text(self, html_content: str) -> str:
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            return soup.get_text(separator="\n")
        except Exception as e:
            print(f"Error extracting HTML text: {e}")
            return ""