from fastapi import Request, Form, APIRouter, status, Security
from fastapi.responses import HTMLResponse, RedirectResponse

from medperf.web_ui.auth import security_token, AUTH_COOKIE_NAME
from medperf.web_ui.common import templates, api_key_cookie

router = APIRouter()


# security check page GET endpoint
@router.get("/security_check", response_class=HTMLResponse)
def security_check_form(
    request: Request, redirect_url: str = "/", token: str = Security(api_key_cookie)
):
    # Check if user is already authenticated
    if token == security_token:
        # User is already authenticated, redirect to original URL
        return RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)
    else:
        # User is not authenticated, show security check form
        return templates.TemplateResponse(
            "security_check.html", {"request": request, "redirect_url": redirect_url}
        )


# security check page POST endpoint
@router.post("/security_check")
def access_web_ui(
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
            "security_check.html",
            {
                "request": request,
                "redirect_url": redirect_url,
                "error": "Invalid token",
            },
        )
