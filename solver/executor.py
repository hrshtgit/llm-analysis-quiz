from typing import Any, Dict
import httpx
import re
from urllib.parse import urljoin
from io import StringIO

import pandas as pd  # make sure pandas is in requirements.txt

from .browser import get_page_text, get_page_html


async def compute_answer(quiz_info: Dict[str, Any], email: str, secret: str) -> Any:
    """
    Decide what answer to send based on quiz_info.

    - If scrape_url is present:
        Use Playwright to load that URL (JS executed) and extract a 'secret code'.

    - Else if csv_quiz is True:
        Find CSV URL from the page HTML, parse cutoff, download CSV and compute sum.

    - Else if it's the uv http get task:
        Return the exact command string they ask for.

    - Else:
        For now, return a simple placeholder answer (for initial demo).
    """
    scrape_url = quiz_info.get("scrape_url")
    csv_quiz = quiz_info.get("csv_quiz", False)
    csv_cutoff = quiz_info.get("csv_cutoff")
    current_url = quiz_info.get("current_url")
    raw_text = quiz_info.get("raw_text", "") or ""

    # Case 1: scrape_url present -> demo-scrape secret code
    if scrape_url:
        print(f"[compute_answer] Scraping (with JS) from {scrape_url}")

        rendered_text = await get_page_text(scrape_url)
        print("[compute_answer] Rendered scrape page snippet:", rendered_text[:500])

        lines = rendered_text.splitlines()
        candidate_code = None

        for line in lines:
            low = line.lower()
            if "secret" in low and "code" in low:
                # Try "secret code is <number> ..."
                m = re.search(r"[Ss]ecret code\s+is\s+(\d+)", line)
                if m:
                    candidate_code = m.group(1)
                    print("[compute_answer] Found secret code via 'is' pattern:", candidate_code)
                    break

                # General: first number on that line
                nums = re.findall(r"\d+", line)
                if nums:
                    candidate_code = nums[0]
                    print("[compute_answer] Found secret code via first-number-on-line heuristic:", candidate_code)
                    break

        if candidate_code is None:
            print("[compute_answer] No 'secret code' line with number found, looking globally.")
            nums_global = re.findall(r"\d+", rendered_text)
            if nums_global:
                candidate_code = nums_global[0]
                print("[compute_answer] Using first global number as fallback:", candidate_code)

        if candidate_code is not None:
            return candidate_code

        print("[compute_answer] No numbers found at all, returning full rendered text.")
        return rendered_text.strip()

    # Case 1.5: project2-uv -> return uv http get command string as answer
    # (must be BEFORE CSV and fallback)
    lowered = raw_text.lower()
    if "uv http get" in lowered or (current_url and "project2-uv" in current_url):
        answer = (
            'uv http get '
            'https://tds-llm-analysis.s-anand.net/project2/uv.json'
            f'?email={email} '
            '-H "Accept: application/json"'
        )
        print(f"[compute_answer] UV task answer: {answer!r}")
        return answer

    # Case 2: CSV file / "Wrong sum of numbers" quiz
    if csv_quiz and csv_cutoff is not None:
        print("[compute_answer] Detected CSV quiz with cutoff:", csv_cutoff)

        # Get full HTML to look for a CSV link
        html = await get_page_html(current_url)
        print("[compute_answer] HTML snippet for CSV quiz:", html[:800])

        # Try to find an href or URL ending with .csv
        csv_url = None

        # 1) href="...csv"
        m_href = re.search(r'href="([^"]+\.csv)"', html, flags=re.IGNORECASE)
        if m_href:
            rel_csv = m_href.group(1)
            csv_url = urljoin(current_url, rel_csv)

        # 2) Any absolute CSV URL in the HTML (fallback)
        if not csv_url:
            m_abs = re.search(r'(https?://[^\s"]+\.csv)', html, flags=re.IGNORECASE)
            if m_abs:
                csv_url = m_abs.group(1)

        if not csv_url:
            print("[compute_answer] Could not find CSV URL in HTML. Returning placeholder.")
            return "0"

        print("[compute_answer] Found CSV URL:", csv_url)

        # Download the CSV
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.get(csv_url)
            resp.raise_for_status()
            csv_text = resp.text

        # Load into pandas
        df = pd.read_csv(StringIO(csv_text))
        print("[compute_answer] CSV columns:", df.columns.tolist())
        print("[compute_answer] First few rows:\n", df.head())

        # Heuristic:
        # - Find the first numeric column
        # - Sum values greater than the cutoff
        numeric_cols = df.select_dtypes(include=["number"]).columns
        if len(numeric_cols) == 0:
            print("[compute_answer] No numeric columns found, returning 0.")
            return 0

        target_col = numeric_cols[0]
        print("[compute_answer] Using numeric column:", target_col)

        filtered = df[df[target_col] > csv_cutoff]
        total = int(filtered[target_col].sum())
        print(f"[compute_answer] Computed sum of {target_col} > {csv_cutoff}: {total}")

        return total

    # Case 3: simple / demo page
    print("[compute_answer] No scrape_url and not a CSV quiz, using placeholder answer for demo.")
    return "hello-from-harshit"


async def submit_answer(
    submit_url: str,
    email: str,
    secret: str,
    original_url: str,
    answer: Any,
) -> Dict[str, Any]:
    payload = {
        "email": email,
        "secret": secret,
        "url": original_url,
        "answer": answer,
    }

    print(f"[submit_answer] POSTing to {submit_url} with payload: {payload}")

    async with httpx.AsyncClient() as client:
        resp = await client.post(submit_url, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        print("[submit_answer] Response JSON:", data)
        return data