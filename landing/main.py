from fastapi import FastAPI, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from tasks import register_user

app = FastAPI()
templates = Jinja2Templates(directory="templates")


@app.get("/")
async def landing(request: Request):
    return templates.TemplateResponse("landing.html", {"request": request})


@app.post("/register")
async def register(
    name: str = Form(...),
    email: str = Form(...),
    role: str = Form(...),
):
    register_user.delay(name, email, role)
    return RedirectResponse(url="/demo", status_code=303)


@app.get("/demo")
async def demo(request: Request):
    return templates.TemplateResponse("demo.html", {"request": request})
