"""
Orchestrator for the quiz solver.

Given a starting URL, this module:
  - fetches the quiz page
  - parses its instructions
  - computes an answer (using scraping / CSV / etc.)
  - submits the answer
  - follows any 'next url' returned by the server
"""
import time
from typing import Optional
from .browser import get_page_text
from .parser import parse_quiz_page
from .executor import compute_answer, submit_answer


async def solve_quiz_session(email: str, secret: str, start_url: str, deadline: float):
    current_url: Optional[str] = start_url

    while current_url and time.time() < deadline:
        print(f"Solving quiz at: {current_url}")

        page_text = await get_page_text(current_url)
        quiz_info = await parse_quiz_page(page_text, current_url)
        answer_obj = await compute_answer(quiz_info, email=email, secret=secret)
        result = await submit_answer(
            submit_url=quiz_info["submit_url"],
            email=email,
            secret=secret,
            original_url=current_url,
            answer=answer_obj,
        )

        print("Quiz result:", result)

        next_url = result.get("url")
        if next_url:
            current_url = next_url
        else:
            break

    print("Quiz session ended.")