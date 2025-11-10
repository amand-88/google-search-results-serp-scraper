import json
from pathlib import Path

from src.parsers.serp_parser import SerpParser

_SAMPLE_HTML = """
<html>
  <body>
    <div id="search">
      <div class="g">
        <div class="yuRUbf"><a href="https://www.nike.com/"><h3>Nike. Just Do It. Nike.com</h3></a></div>
        <div class="IsZvec"><span class="aCOpRe">Discover the latest shoes, apparel and accessories.</span></div>
      </div>
      <div class="g">
        <div class="yuRUbf"><a href="https://en.wikipedia.org/wiki/Nike,_Inc."><h3>Nike - Wikipedia</h3></a></div>
        <div class="VwiC3b">Nike, Inc. is an American...</div>
      </div>
      <!-- Duplicate should be de-duped -->
      <div class="g">
        <div class="yuRUbf"><a href="https://www.nike.com/"><h3>Nike. Just Do It. Nike.com</h3></a></div>
        <div class="IsZvec">Shop now.</div>
      </div>
    </div>
  </body>
</html>
"""

def test_parser_extracts_unique_results(tmp_path: Path):
    parser = SerpParser()
    results = parser.parse(_SAMPLE_HTML)
    assert isinstance(results, list)
    assert len(results) == 2
    assert results[0]["title"].startswith("Nike")
    assert results[0]["url"] == "https://www.nike.com/"
    assert "description" in results[0]
    # Ensure JSON serializable
    json.dumps(results)