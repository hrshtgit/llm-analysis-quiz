from typing import Dict, Any
import re
from urllib.parse import urljoin


async def parse_quiz_page(page_text: str, current_url: str) -> Dict[str, Any]:
    """
    Extract:
      - submit_url : where to POST the answer
      - scrape_url : optional, where to GET extra data (demo-scrape)
      - csv_cutoff : optional, for CSV/sum quiz
    """

    submit_url = None

    # 1) Try absolute URL pattern
    m_abs = re.search(
        r"Post your answer to\s+(https?://\S+)",
        page_text,
        flags=re.IGNORECASE,
    )
    if m_abs:
        submit_url = m_abs.group(1)

    # 2) Generic "POST ... to /something"
    if not submit_url:
        m_post_to = re.search(
            r"POST\s+.*?\s+to\s+(\S+)",
            page_text,
            flags=re.IGNORECASE,
        )
        if m_post_to:
            rel = m_post_to.group(1)
            submit_url = urljoin(current_url, rel)

    if not submit_url:
        print("Could not find submit URL. Page text snippet:")
        print(page_text[:500])
        raise ValueError("Submit URL not found on quiz page")

    # 3) Look for a scrape URL (demo-scrape)
    scrape_url = None
    m_scrape = re.search(
        r"Scrape\s+(\S+)\s+\(relative to this page\)",
        page_text,
        flags=re.IGNORECASE,
    )
    if m_scrape:
        rel_scrape = m_scrape.group(1)
        scrape_url = urljoin(current_url, rel_scrape)

    # 4) Detect CSV/sum quiz and cutoff
    csv_cutoff = None
    csv_quiz = False
    if "csv file" in page_text.lower():
        csv_quiz = True
        m_cutoff = re.search(
            r"Cutoff:\s*(\d+)",
            page_text,
            flags=re.IGNORECASE,
        )
        if m_cutoff:
            csv_cutoff = int(m_cutoff.group(1))

    quiz_info: Dict[str, Any] = {
        "submit_url": submit_url,
        "scrape_url": scrape_url,   # may be None
        "csv_cutoff": csv_cutoff,   # may be None
        "csv_quiz": csv_quiz,
        "answer_type": "string",
        "raw_text": page_text,
        "current_url": current_url,
    }

    print("[parse_quiz_page] Parsed quiz_info:", quiz_info)
    return quiz_info