import bcrypt
from fastapi import APIRouter, Cookie, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from auth import SECURE_COOKIES, create_token, decode_token
from db import get_user_by_email

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/login")
async def login_page(request: Request, access_token: str | None = Cookie(default=None)):
    if access_token:
        try:
            decode_token(access_token)
            return RedirectResponse(url="/dashboard", status_code=303)
        except Exception:
            pass
    error = request.query_params.get("error")
    return templates.TemplateResponse("login.html", {"request": request, "error": error})


@router.post("/login")
async def login(
    email: str = Form(...),
    password: str = Form(...),
):
    user = get_user_by_email(email)
    if not user or "password_hash" not in user:
        return RedirectResponse(url="/login?error=1", status_code=303)
    if not bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
        return RedirectResponse(url="/login?error=1", status_code=303)

    token = create_token(user["email"], user["role"])
    response = RedirectResponse(url="/dashboard", status_code=303)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=SECURE_COOKIES,
    )
    return response


@router.post("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("access_token")
    return response
