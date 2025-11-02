from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import os

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

@app.get("/state")
def get_state():
    return JSONResponse(content=_timer.get_state())

@app.post("/start")
async def start(req: Request):
    payload = await req.json()
    work = int(payload.get("work_min", 25))
    short = int(payload.get("short_min", 5))
    long = int(payload.get("long_min", 15))
    cycle = int(payload.get("pomos_per_cycle", 4))
    _timer.start(work, short, long, cycle)
    return JSONResponse(content=_timer.get_state())

@app.post("/pause")
def pause():
    _timer.pause()
    return JSONResponse(content=_timer.get_state())

@app.post("/resume")
def resume():
    _timer.resume()
    return JSONResponse(content=_timer.get_state())

@app.post("/toggle_pause")
def toggle_pause():
    _timer.toggle_pause()
    return JSONResponse(content=_timer.get_state())

@app.post("/skip")
def skip():
    _timer.skip()
    return JSONResponse(content=_timer.get_state())

@app.post("/stop")
def stop():
    _timer.stop()
    return JSONResponse(content=_timer.get_state())

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