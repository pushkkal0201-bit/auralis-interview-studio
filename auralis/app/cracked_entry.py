"""Optional Auralis entry point exposing the Cracked skill hub.

Run: python -m uvicorn app.cracked_entry:app --host 127.0.0.1 --port 8000
The original app.main:app entry point remains unchanged.
"""
import re

from fastapi import Depends, HTTPException, Request
from fastapi.responses import FileResponse

from .main import app, owner_hash, STATIC
from .cracked_suite import CoachRequest, INDEX, coach, feature_catalog


def current_owner(request: Request):
    """Match Auralis's authentication mode without inventing a public session."""
    auth = app.state.auth
    if auth is not None:
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            raise HTTPException(401, "Sign in to Auralis first.")
        user = auth.user(header.removeprefix("Bearer ").strip())
        return owner_hash("supabase:" + str(user["id"]))
    token = request.headers.get("X-Owner-Token", "")
    if not re.fullmatch(r"[a-f0-9]{64}", token):
        raise HTTPException(401, "Open the Auralis application in this browser first.")
    return owner_hash(token)


@app.get("/cracked")
def cracked_hub():
    return FileResponse(STATIC / "cracked.html")


@app.get("/api/cracked/features")
def cracked_features(user=Depends(current_owner)):
    return {
        "features": feature_catalog(),
        "method": "native-tools-plus-guidance",
        "disclaimer": "Guidance is not an executed agent workflow. Some features still require tools and integration.",
    }


@app.post("/api/cracked/coach")
async def cracked_coach(request_data: CoachRequest, user=Depends(current_owner)):
    if request_data.skill not in INDEX:
        raise HTTPException(404, "Unknown skill.")
    if not request_data.consent:
        raise HTTPException(422, "Consent is required before sending input to Groq.")
    app.state.engine.usage_budget.consume(user)
    try:
        return await coach(app.state.engine.live, request_data)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
