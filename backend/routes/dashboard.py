from fastapi import APIRouter, Cookie, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from auth import decode_token
from db import get_all_users, delete_user_by_email
from dependencies import require_admin


router = APIRouter()
templates = Jinja2Templates(directory="templates")


def _auth(access_token: str | None = Cookie(default=None)) -> dict | None:
    if not access_token:
        return None
    try:
        return decode_token(access_token)
    except Exception:
        return None


@router.get("/dashboard")
async def dashboard(request: Request, user: dict | None = Depends(_auth)):
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user})


@router.get("/admin/users")
async def admin_users(user: dict = Depends(require_admin)):
    users = get_all_users()
    # strip password hashes before returning
    return [
        {k: v for k, v in u.items() if k != "password_hash"}
        for u in users
    ]

@router.delete("/admin/users/{email}")
async def delete_user(email: str, user: dict = Depends(require_admin)):
    delete_user_by_email(email)
    return {"ok": True}