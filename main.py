from fastapi import FastAPI, Request, Form, BackgroundTasks, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
from pydantic import BaseModel
import os

app = FastAPI(title="AI Data Platform")

templates = Jinja2Templates(directory="templates")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup: This runs ONCE when the server starts
    db_client = DatabaseClient()
    db_client.connected = True
    
    # Store it in the app state so any route can access this EXACT single instance
    app.state.db = db_client
    
    yield

app = FastAPI(lifespan=lifespan)

@app.get("/", response_class=HTMLResponse)
async def serve_dashboard(request: Request):


    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/history", response_class=HTMLResponse)
async def history_page(request: Request):
    return templates.TemplateResponse("history.html", {"request": request})

@app.get("/investigate", response_class=HTMLResponse)
