# file: web_search/search.py
# Haven web search engine - searches the web and fetches content for knowledge

import re
from datetime import datetime

try:
    from duckduckgo_search import DDGS
    _DDGS_AVAILABLE = True
except ImportError:
    _DDGS_AVAILABLE = False

try:
    import urllib.request
    import urllib.parse
    import ssl
    _URllib_AVAILABLE = True
except ImportError:
    _URllib_AVAILABLE = False


class WebSearch:
    """
    Web search engine for Haven. Allows searching the web for information
    and fetching webpage content to help answer questions Haven doesn't know.
    """

    def __init__(self, max_results: int = 5, search_timeout: int = 10):
        self.max_results = max_results
        self.search_timeout = search_timeout
        self.ddgs = None
        self.available = False
        self.search_history = []  # Track recent searches to avoid duplicates

        if _DDGS_AVAILABLE:
            try:
                self.ddgs = DDGS()
                self.available = True
                print("[WebSearch] DuckDuckGo search loaded.")
            except Exception as e:
                print(f"[WebSearch] Failed to load DuckDuckGo: {e}")
        else:
            print("[WebSearch] duckduckgo-search not installed. Web search disabled.")
            print("[WebSearch] Install with: pip install duckduckgo-search")

    def search(self, query: str, max_results: int = None) -> list:
        """
        Search the web for a query and return results.

        Args:
            query: Search query string
            max_results: Maximum number of results (default: self.max_results)

        Returns:
            List of dicts with 'title', 'url', and 'snippet' keys
        """
        if not self.available:
            print("[WebSearch] Search unavailable — duckduckgo-search not installed.")
            return []

        if max_results is None:
            max_results = self.max_results

        # Avoid duplicate searches within recent history
        query_lower = query.lower().strip()
        for recent in self.search_history[-20:]:
            if recent["query"].lower() == query_lower:
                print(f"[WebSearch] Returning cached results for: {query}")
                return recent["results"]

        try:
            results = self.ddgs.text(query, max_results=max_results, timeout=self.search_timeout)

            # Filter results to only include those with useful snippets
            filtered = []
            for r in results:
                if r.get("body") or r.get("snippet"):
                    filtered.append({
                        "title": r.get("title", ""),
                        "url": r.get("href", r.get("url", "")),
                        "snippet": r.get("body", r.get("snippet", ""))
                    })

            # Cache the results
            self.search_history.append({
                "query": query,
                "results": filtered,
                "timestamp": datetime.now().isoformat()
            })

            print(f"[WebSearch] Found {len(filtered)} results for: {query}")
            return filtered

        except Exception as e:
            print(f"[WebSearch] Search error: {e}")
            return []

    def fetch_content(self, url: str, max_length: int = 3000) -> str:
        """
        Fetch and extract text content from a webpage.

        Args:
            url: URL to fetch
            max_length: Maximum characters to return

        Returns:
            Extracted text content, or empty string on failure
        """
        if not _URllib_AVAILABLE:
            return ""

        try:
            # Create SSL context that ignores cert errors for local/dev use
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

            # Set headers to mimic a browser
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
            }

            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10, context=ctx) as response:
                html = response.read().decode("utf-8", errors="ignore")

            # Extract text from HTML
            text = self._extract_text_from_html(html)

            # Truncate if too long
            if len(text) > max_length:
                text = text[:max_length] + "..."

            print(f"[WebSearch] Fetched {len(text)} chars from: {url}")
            return text.strip()

        except Exception as e:
            print(f"[WebSearch] Failed to fetch {url}: {e}")
            return ""

    def _extract_text_from_html(self, html: str) -> str:
        """Extract readable text from HTML content."""
        # Remove script and style elements
        text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)

        # Remove HTML comments
        text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)

        # Replace common HTML tags with newlines
        text = re.sub(r"<br\s*/?>", "\n", text)
        text = re.sub(r"<p[^>]*>", "\n", text)
        text = re.sub(r"</p>", "\n", text)
        text = re.sub(r"<div[^>]*>", "\n", text)
        text = re.sub(r"<li>", "\n  - ", text)
        text = re.sub(r"<h[1-6][^>]*>", "\n\n", text)
        text = re.sub(r"</h[1-6]>", "\n", text)

        # Remove all remaining HTML tags
        text = re.sub(r"<[^>]+>", "", text)

        # Decode common HTML entities
        entities = {
            "&amp;": "&", "&lt;": "<", "&gt;": ">", "&quot;": '"',
            "&#39;": "'", "&nbsp;": " ", "&mdash;": "—", "&ndash;": "–",
        }
        for entity, char in entities.items():
            text = text.replace(entity, char)

        # Clean up whitespace
        lines = [line.strip() for line in text.split("\n")]
        lines = [line for line in lines if line]
        text = "\n".join(lines)

        return text

    def search_and_summarize(self, query: str, fetch_top: int = 2) -> str:
        """
        Search the web and fetch content from top results to create a summary.

        Args:
            query: Search query
            fetch_top: Number of top results to fetch content from

        Returns:
            Combined text from search snippets and fetched content
        """
        results = self.search(query)
        if not results:
            return ""

        # Start with snippets
        parts = []
        parts.append(f"Search results for '{query}':")

        for i, result in enumerate(results):
            parts.append(f"\n--- Result {i+1}: {result['title']} ---")
            parts.append(f"URL: {result['url']}")
            parts.append(f"Snippet: {result['snippet']}")

            # Fetch full content for top results
            if i < fetch_top and result["url"]:
                content = self.fetch_content(result["url"], max_length=2000)
                if content:
                    parts.append(f"Content: {content}")

        return "\n".join(parts)

    def should_search(self, user_query: str) -> bool:
        """
        Heuristic check to determine if a query might benefit from web search.

        Args:
            user_query: User's question or statement

        Returns:
            True if web search might help answer the query
        """
        query_lower = user_query.lower()

        # Keywords that suggest web search would help
        search_indicators = [
            "how to", "what is", "who is", "when did", "where is",
            "latest", "recent", "new", "current", "today",
            "tutorial", "guide", "example", "code", "programming",
            "install", "setup", "configure", "fix", "error",
            "python", "javascript", "react", "api", "library",
            "download", "update", "version", "release",
            "weather", "news", "price", "stock",
            "search", "find", "look up", "web", "internet",
            "website", "url", "link",
        ]

        # Questions that definitely need search
        question_patterns = [
            r"\bhow\s+to\b", r"\bwhat\s+is\b", r"\bwho\s+is\b",
            r"\blatest\b", r"\bcurrent\b", r"\btoday\b",
            r"\btutorial\b", r"\bexample\b", r"\berror\b",
            r"\binstall\b", r"\bfix\b",
        ]

        # Check for question patterns
        for pattern in question_patterns:
            if re.search(pattern, query_lower):
                return True

        # Check for search keywords
        for keyword in search_indicators:
            if keyword in query_lower:
                return True

        # Check if it's a question about something specific
        if "?" in user_query and len(user_query) > 15:
            return True

        return False

    def clear_history(self):
        """Clear search history."""
        self.search_history = []
        print("[WebSearch] Search history cleared.")
