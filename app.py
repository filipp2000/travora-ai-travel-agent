import logging
import traceback
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from backend import (
    checkpointer,
    db_pool,
    run_travel_agent,
)
from pydantic_models.api_request import TravelRequestBody
from pydantic_models.api_response import TravelResponse
from services.session_lifecycle import SessionConflictError

logger = logging.getLogger(__name__)


BASE_DIR = Path(__file__).resolve().parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code: Open the database connection pool.
    db_pool.open()

    try:
        checkpointer.setup()
        yield

    finally:
        # Shutdown code: Close the database connection pool.
        db_pool.close()


# FastAPI initialization
app = FastAPI(
    title="Travel Agent",
    description="LangGraph Multi-Agent Travel Planner that helps users plan trips, find flights and hotels, and create itineraries.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health_check():
    # Simple endpoint used to verify that the API is running.
    return {"status": "ok", "message": "The Travel Agent API is running."}


@app.get("/favicon.ico")
async def favicon():
    return JSONResponse(content={})


app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


class TravelRequest(BaseModel):
    # Pydantic schema expected from the client request body.
    message: str
    thread_id: str | None = None


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={})


@app.post("/api/travel", response_model=TravelResponse)
async def travel_planner(request_data: TravelRequestBody):
    try:
        # Request validation is handled by TravelRequestBody.
        result = run_travel_agent(
            user_input=request_data.message,
            thread_id=request_data.thread_id,
            action=request_data.action,
        )

        return TravelResponse.model_validate(result)

    except SessionConflictError as exc:
        # Unknown, completed or cancelled threads
        # cannot receive clarification replies.
        return JSONResponse(
            status_code=409,
            content={
                "success": False,
                "error": str(exc),
            },
        )

    except Exception:
        # Keep error details in server logs,
        # not in API response.
        logger.exception("Travel request failed")

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": ("An unexpected error occurred. Please try again."),
            },
        )


if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
