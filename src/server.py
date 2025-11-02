from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
import os
import json
import asyncio
import signal
import sys
from typing import Optional

from timer import Timer
from audio import Audio
from notifier import Notifier

app = FastAPI(title="Pomodoro Timer API")

# Timer singleton used by the API
_timer = Timer(audio=Audio(), notifier=Notifier())

# Serve the static UI directory
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# API key from env (optional). If set, endpoints require x-api-key header or api_key query param.
API_KEY = os.environ.get("POMODORO_API_KEY")


def verify_api_key_from_request(request: Request) -> None:
    """Raise HTTPException if API key is required and not provided / invalid."""
    if not API_KEY:
        return  # no auth required
    # accept header or query param (EventSource cannot send custom headers reliably)
    header_key = request.headers.get("x-api-key")
    query_key = request.query_params.get("api_key")
    if header_key == API_KEY or query_key == API_KEY:
        return
    raise HTTPException(status_code=401, detail="Unauthorized")


# Basic API endpoints (use verify_api_key_from_request where needed)
@app.get("/state")
def get_state(request: Request):
    verify_api_key_from_request(request)
    return JSONResponse(content=_timer.get_state())


@app.post("/start")
async def start(request: Request):
    verify_api_key_from_request(request)
    payload = await request.json()
    work = int(payload.get("work_min", 25))
    short = int(payload.get("short_min", 5))
    long = int(payload.get("long_min", 15))
    cycle = int(payload.get("pomos_per_cycle", 4))
    _timer.start(work, short, long, cycle)
    return JSONResponse(content=_timer.get_state())


@app.post("/pause")
def pause(request: Request):
    verify_api_key_from_request(request)
    _timer.pause()
    return JSONResponse(content=_timer.get_state())


@app.post("/resume")
def resume(request: Request):
    verify_api_key_from_request(request)
    _timer.resume()
    return JSONResponse(content=_timer.get_state())


@app.post("/toggle_pause")
def toggle_pause(request: Request):
    verify_api_key_from_request(request)
    _timer.toggle_pause()
    return JSONResponse(content=_timer.get_state())


@app.post("/skip")
def skip(request: Request):
    verify_api_key_from_request(request)
    _timer.skip()
    return JSONResponse(content=_timer.get_state())


@app.post("/stop")
def stop(request: Request):
    verify_api_key_from_request(request)
    _timer.stop()
    return JSONResponse(content=_timer.get_state())


# Server-Sent Events endpoint for real-time updates
@app.get("/events")
async def events(request: Request):
    # allow api_key via query param for EventSource
    verify_api_key_from_request(request)

    async def event_generator():
        try:
            while True:
                if await request.is_disconnected():
                    break
                state = _timer.get_state()
                data = json.dumps(state)
                # SSE event named "state"
                yield f"event: state\ndata: {data}\n\n"
                await asyncio.sleep(1.0)
        except asyncio.CancelledError:
            return

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# optional root static file (simple UI)
index_path = os.path.join(static_dir, "index.html")
if os.path.isfile(index_path):
    @app.get("/")
    def root():
        return FileResponse(index_path)
else:
    @app.get("/")
    def root():
        return {"msg": "Place a static/index.html in src/static to use the web UI."}


@app.on_event("shutdown")
async def _shutdown_event():
    """Ensure timer threads are stopped when FastAPI shuts down."""
    try:
        _timer.stop()
    except Exception:
        pass


def _pid_info() -> dict:
    """Return simple PID debug info."""
    try:
        return {"pid": os.getpid(), "ppid": os.getppid(), "pgid": os.getpgrp()}
    except Exception:
        return {"pid": os.getpid(), "ppid": os.getppid()}

@app.get("/debug/pids")
def debug_pids(request: Request):
    """Return PID info (requires API key when configured)."""
    verify_api_key_from_request(request)
    return JSONResponse(content=_pid_info())

def _on_signal(signum, frame):
    """Handle SIGINT/SIGTERM: print debug info, stop timer, and exit."""
    try:
        print(f"Signal {signum} received. PID info: {_pid_info()}", flush=True)
    except Exception:
        pass
    try:
        _timer.stop()
    except Exception:
        pass
    # Ensure process exits
    try:
        sys.exit(0)
    except SystemExit:
        os._exit(0)

# Register signal handlers (best-effort; may be overridden by uvicorn's manager when --reload is used)
for s in (signal.SIGINT, signal.SIGTERM):
    try:
        signal.signal(s, _on_signal)
    except Exception:
        # some environments (Windows service, restricted exec) may not allow signal setup
        pass
