from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from routers import auth, tasks, stats

app = FastAPI(title="ToDo Web App")

app.include_router(auth.router)
app.include_router(tasks.router)
app.include_router(stats.router)

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


@app.get("/")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/tasks-page")
async def tasks_page(request: Request):
    return templates.TemplateResponse("tasks.html", {"request": request})
