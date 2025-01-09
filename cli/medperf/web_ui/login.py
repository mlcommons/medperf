from fastapi import Request, Form, APIRouter, status, Security
from fastapi.responses import HTMLResponse, RedirectResponse

from medperf.web_ui.auth import security_token, AUTH_COOKIE_NAME
from medperf.web_ui.common import templates, api_key_cookie

router = APIRouter()


# Login page GET endpoint
@router.get("/login", response_class=HTMLResponse)
def login_form(
    request: Request, redirect_url: str = "/", token: str = Security(api_key_cookie)
):
    # Check if user is already authenticated
    if token == security_token:
        # User is already authenticated, redirect to original URL
        return RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)
    else:
        # User is not authenticated, show login form
        return templates.TemplateResponse(
            "login.html", {"request": request, "redirect_url": redirect_url}
        )


# Login page POST endpoint
@router.post("/login")
def login(
    request: Request,
    token: str = Form(...),
    redirect_url: str = Form("/"),
):
    if token == security_token:
        response = RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)
        response.set_cookie(key=AUTH_COOKIE_NAME, value=token)
        return response
    else:
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "redirect_url": redirect_url,
                "error": "Invalid token",
            },
        )
