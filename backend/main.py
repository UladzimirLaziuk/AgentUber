from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from routes.auth import router as auth_router
from routes.dashboard import router as dashboard_router

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(auth_router)
app.include_router(dashboard_router)

@app.exception_handler(401)
async def unauthorized(_: Request, __: HTTPException):
    return RedirectResponse(url="/login", status_code=303)

@app.get("/")
async def root():
    return RedirectResponse(url="/dashboard", status_code=303)