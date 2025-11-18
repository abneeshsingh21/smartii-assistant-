"""
Web Search and RAG Module for SMARTII
Provides real-time web search and retrieval capabilities
"""

import logging
from typing import Dict, Any, List, Optional
from duckduckgo_search import DDGS
from bs4 import BeautifulSoup
import requests
from datetime import datetime

logger = logging.getLogger(__name__)


class WebSearchEngine:
    """Advanced web search with RAG capabilities"""
    
    def __init__(self):
        self.ddgs = DDGS()
        self.max_results = 5
        self.timeout = 10
        
    def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Perform web search and return results
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            List of search results with title, url, snippet
        """
        try:
            logger.info(f"Searching web for: {query}")
            
            results = []
            search_results = self.ddgs.text(query, max_results=max_results)
            
            for result in search_results:
                results.append({
                    "title": result.get("title", ""),
                    "url": result.get("href", ""),
                    "snippet": result.get("body", ""),
                    "source": "DuckDuckGo"
                })
            
            logger.info(f"Found {len(results)} search results")
            return results
            
        except Exception as e:
            logger.error(f"Web search error: {e}")
            return []
    
    def search_news(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Search for news articles"""
        try:
            logger.info(f"Searching news for: {query}")
            
            results = []
            news_results = self.ddgs.news(query, max_results=max_results)
            
            for result in news_results:
                results.append({
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "snippet": result.get("body", ""),
                    "date": result.get("date", ""),
                    "source": result.get("source", "Unknown")
                })
            
            return results
            
        except Exception as e:
            logger.error(f"News search error: {e}")
            return []
    
    def search_images(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Search for images"""
        try:
            logger.info(f"Searching images for: {query}")
            
            results = []
            image_results = self.ddgs.images(query, max_results=max_results)
            
            for result in image_results:
                results.append({
                    "title": result.get("title", ""),
                    "url": result.get("image", ""),
                    "thumbnail": result.get("thumbnail", ""),
                    "source": result.get("source", "")
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Image search error: {e}")
            return []
    
    def fetch_webpage_content(self, url: str) -> Optional[str]:
        """
        Fetch and extract text content from a webpage
        
        Args:
            url: URL to fetch
            
        Returns:
            Extracted text content or None
        """
        try:
            logger.info(f"Fetching content from: {url}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text
            text = soup.get_text()
            
            # Clean up text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            # Limit to first 1000 words
            words = text.split()[:1000]
            content = ' '.join(words)
            
            logger.info(f"Extracted {len(words)} words from {url}")
            return content
            
        except Exception as e:
            logger.error(f"Error fetching webpage: {e}")
            return None
    
    def answer_question_with_rag(self, question: str) -> Dict[str, Any]:
        """
        Answer question using RAG (Retrieval Augmented Generation)
        
        Args:
            question: User's question
            
        Returns:
            Dictionary with answer, sources, and context
        """
        try:
            logger.info(f"RAG query: {question}")
            
            # Step 1: Search web for relevant information
            search_results = self.search(question, max_results=3)
            
            if not search_results:
                return {
                    "answer": "I couldn't find any information about that. Could you rephrase your question?",
                    "sources": [],
                    "context": ""
                }
            
            # Step 2: Fetch content from top results
            contexts = []
            sources = []
            
            for result in search_results[:2]:  # Top 2 results
                content = self.fetch_webpage_content(result["url"])
                if content:
                    contexts.append(content)
                    sources.append({
                        "title": result["title"],
                        "url": result["url"]
                    })
            
            # Step 3: Combine contexts
            combined_context = " ".join(contexts)
            
            # Step 4: Generate answer from context
            answer = self._generate_answer_from_context(question, combined_context, search_results)
            
            return {
                "answer": answer,
                "sources": sources,
                "context": combined_context[:500],  # First 500 chars
                "search_results": search_results
            }
            
        except Exception as e:
            logger.error(f"RAG error: {e}")
            return {
                "answer": "I encountered an error while searching for information.",
                "sources": [],
                "context": ""
            }
    
    def _generate_answer_from_context(self, question: str, context: str, search_results: List[Dict]) -> str:
        """Generate answer from retrieved context"""
        try:
            # Extract most relevant snippets
            snippets = []
            for result in search_results[:3]:
                if result.get("snippet"):
                    snippets.append(result["snippet"])
            
            # Combine snippets into answer
            if snippets:
                answer = " ".join(snippets)
                # Limit to 300 characters
                if len(answer) > 300:
                    answer = answer[:297] + "..."
                return answer
            else:
                return "Based on my search, I found information but couldn't extract a clear answer. Please try rephrasing your question."
                
        except Exception as e:
            logger.error(f"Answer generation error: {e}")
            return "I found some information but had trouble processing it."


# Global instance
_web_search_engine = None


def get_web_search_engine() -> WebSearchEngine:
    """Get or create global web search engine instance"""
    global _web_search_engine
    if _web_search_engine is None:
        _web_search_engine = WebSearchEngine()
    return _web_search_engine
