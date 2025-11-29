import os
import time

from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse

from solver.orchestrator import solve_quiz_session

load_dotenv()

app = FastAPI()

SECRET_KEY = os.getenv("SECRET_KEY")
MY_EMAIL = os.getenv("MY_EMAIL")

if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY not set in .env")
if not MY_EMAIL:
    raise RuntimeError("MY_EMAIL not set in .env")


@app.post("/")
async def handle_quiz(request: Request):
    """
    Main endpoint for the quiz system.

    - Parse JSON body
    - Validate required fields
    - Check secret
    - Run solve_quiz_session (which handles URL chain, scraping, CSV, etc.)
    - Return 200 on acceptance
    """

    # 1) Parse JSON safely
    try:
        payload = await request.json()
    except Exception:
        # Project spec: 400 for invalid JSON
        raise HTTPException(status_code=400, detail="Invalid JSON")

    email = payload.get("email")
    secret = payload.get("secret")
    url = payload.get("url")

    # 2) Basic validation
    if not isinstance(email, str) or not isinstance(secret, str) or not isinstance(url, str):
        raise HTTPException(status_code=400, detail="Missing or invalid fields")

    # 3) Secret check
    if secret != SECRET_KEY:
        raise HTTPException(status_code=403, detail="Forbidden: invalid secret")

    # 4) Run quiz solving pipeline (synchronously)
    # We set a deadline 3 minutes from now, as per project requirement.
    deadline = time.time() + 180.0

    try:
        await solve_quiz_session(email=email, secret=secret, start_url=url, deadline=deadline)
    except Exception as e:
        # For safety, log and surface a 500 if something really breaks
        print("[handle_quiz] Error during solve_quiz_session:", repr(e))
        raise HTTPException(status_code=500, detail="Internal error during quiz solving")

    # 5) If we got here, we at least attempted within the deadline
    return JSONResponse({"status": "ok"})