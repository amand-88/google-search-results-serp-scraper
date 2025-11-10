from __future__ import annotations

from bs4 import BeautifulSoup
from typing import List, Dict

class SerpParser:
    """
    Parse Google HTML into a structured list of organic results.
    Tries multiple robust selectors to withstand minor DOM changes.
    """

    def parse(self, html: str) -> List[Dict]:
        soup = BeautifulSoup(html, "lxml")

        results: List[Dict] = []

        # Primary: standard organic blocks
        # Each organic result often has a title in <h3> and link in .yuRUbf > a
        candidates = soup.select("div#search div.g, div#search div[data-header-feature='0']") or soup.select("div#search .MjjYud")

        for node in candidates:
            # URL & Title
            url = None
            title = None

            # Common pattern
            a_tag = node.select_one(".yuRUbf > a")
            title_tag = node.select_one("h3")

            if a_tag and a_tag.get("href"):
                url = a_tag.get("href")
            elif node.select_one("a"):
                url = node.select_one("a").get("href")

            if title_tag and title_tag.text.strip():
                title = title_tag.text.strip()
            elif a_tag and a_tag.text.strip():
                title = a_tag.text.strip()

            # Snippet
            desc_tag = node.select_one("div.VwiC3b") or node.select_one("div.IsZvec")
            description = desc_tag.get_text(" ", strip=True) if desc_tag else ""

            if url and title:
                results.append(
                    {
                        "position": None,  # Filled later in main; keep placeholder
                        "title": title,
                        "url": url,
                        "description": description,
                    }
                )

        # De-dup by URL, preserving order
        seen = set()
        unique_results: List[Dict] = []
        for r in results:
            if r["url"] not in seen:
                unique_results.append(r)
                seen.add(r["url"])

        return unique_results