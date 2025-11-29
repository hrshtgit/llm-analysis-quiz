# LLM Analysis Quiz – Backend

This repository contains my solution for the IITM TDS Project 2 **LLM Analysis Quiz**.

It exposes a single FastAPI endpoint that receives a quiz URL, automatically solves a sequence of data-related tasks (scraping, parsing, CSV analysis), and submits answers back to the quiz server.

---

## API Endpoint

`POST /`

### Request body

```json
{
  "email": "your-email@example.com",
  "secret": "your-secret",
  "url": "https://example.com/quiz-123"
}
	•	email – my registered IITM email.
	•	secret – a secret string I provided in the Google Form.
	•	url – starting quiz URL sent by the evaluator.

Responses
	•	200 OK – accepted and started solving the quiz.
	•	400 Bad Request – invalid JSON or missing / invalid fields.
	•	403 Forbidden – secret does not match my configured secret.

High-level design
	•	app.py
	•	FastAPI app definition.
	•	Validates request JSON and secret.
	•	Sets a 3-minute deadline and calls solve_quiz_session(...).
	•	solver/orchestrator.py
	•	Main loop for the quiz:
	•	Fetches the current quiz URL.
	•	Parses quiz instructions (submit URL, scrape URL, CSV cutoff, etc.).
	•	Calls compute_answer(...) to produce an answer.
	•	Submits the answer as JSON to the quiz server.
	•	Follows any url returned in the response until the quiz ends.
	•	solver/browser.py
	•	Uses Playwright in headless mode to render JavaScript pages.
	•	Returns the fully rendered HTML so that hidden text (e.g. atob(...)) is visible.
	•	solver/parser.py
	•	Parses the rendered HTML and extracts structured info:
	•	submit_url – where to POST the answer.
	•	scrape_url – extra URL to scrape if the question says so.
	•	csv_quiz + csv_cutoff – flags for the CSV-based quiz.
	•	raw question text.
	•	solver/executor.py
	•	Implements specific solver logic:
	•	Demo quiz: returns a placeholder answer.
	•	Secret-code quiz: scrapes a second page and extracts the “Secret code is …” value.
	•	CSV quiz: downloads the CSV, loads it with pandas, and computes the required numeric result.
