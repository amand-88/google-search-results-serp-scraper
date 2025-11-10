import random
import time
from typing import Dict, Optional, Tuple

import requests

# A small set of modern desktop user agents to rotate over.
_UA_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
]

class RequestManager:
    def __init__(
        self,
        *,
        base_url: str,
        timeout: int = 15,
        retries: int = 2,
        backoff: float = 1.0,
        default_params: Optional[Dict] = None,
        default_headers: Optional[Dict] = None,
    ) -> None:
        self.base_url = base_url
        self.timeout = timeout
        self.retries = retries
        self.backoff = backoff
        self.default_params = default_params or {"num": 10}
        self.default_headers = default_headers or {}

    def build_query(
        self,
        *,
        query: str,
        gl: Optional[str],
        hl: Optional[str],
        tbs: Optional[str],
        start: int,
        num: int,
    ) -> Tuple[str, Dict]:
        params: Dict[str, Optional[str | int]] = {
            "q": query,
            "start": start,
            "num": num,
            "gl": gl,
            "hl": hl,
            "tbs": tbs,
            "uule": None,  # left for advanced geo encoding if needed
        }
        # Merge defaults but allow direct overrides
        merged = {**self.default_params, **{k: v for k, v in params.items() if v is not None}}
        return self.base_url, merged

    def get(self, url: str, *, params: Dict) -> str:
        last_exc = None
        for attempt in range(self.retries + 1):
            try:
                headers = {
                    "User-Agent": random.choice(_UA_POOL),
                    "Accept-Language": params.get("hl", "en-US,en;q=0.9"),
                    "Cache-Control": "no-cache",
                    **self.default_headers,
                }
                resp = requests.get(url, params=params, headers=headers, timeout=self.timeout)
                if resp.status_code == 429:
                    # Back off harder for rate limiting
                    time.sleep(self.backoff * (attempt + 1) * 2)
                    continue
                resp.raise_for_status()
                return resp.text
            except Exception as e:
                last_exc = e
                time.sleep(self.backoff * (attempt + 1))
        raise RuntimeError(f"Failed to fetch SERP after {self.retries + 1} attempts: {last_exc}")