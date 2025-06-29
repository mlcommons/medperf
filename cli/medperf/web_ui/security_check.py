from fastapi import Request, Form, APIRouter, status, Security
from fastapi.responses import HTMLResponse, RedirectResponse

from medperf.web_ui.auth import security_token, AUTH_COOKIE_NAME
from medperf.web_ui.common import templates, api_key_cookie
from urllib.parse import urlparse

router = APIRouter()


def sanitize_redirect_url(url: str, fallback: str = "/") -> bool:
    """Validate that the URL is a relative path or matches allowed hosts."""
    normalized_url = url.replace("\\", "")  # Normalize backslashes
    parsed = urlparse(normalized_url)
    if not parsed.netloc and not parsed.scheme:
        return normalized_url
    return fallback


# security check page GET endpoint
@router.get("/security_check", response_class=HTMLResponse)
def security_check_form(
    request: Request, redirect_url: str = "/", token: str = Security(api_key_cookie)
):
    # Check if user is already authenticated
    if token == security_token:
        # User is already authenticated, redirect to original URL
        sanitized_redirect_url = sanitize_redirect_url(redirect_url)
        return RedirectResponse(
            url=sanitized_redirect_url, status_code=status.HTTP_302_FOUND
        )

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
    sanitized_redirect_url = sanitize_redirect_url(redirect_url)
    if token == security_token:
        response = RedirectResponse(
            url=sanitized_redirect_url, status_code=status.HTTP_302_FOUND
        )

        response.set_cookie(
            key=AUTH_COOKIE_NAME,
            value=security_token,
            secure=True,
            httponly=True,
            samesite="strict",
            max_age=60 * 60 * 24 * 365,  # 1 year
        )
        return response
    else:
        return templates.TemplateResponse(
            "security_check.html",
            {
                "request": request,
                "redirect_url": sanitized_redirect_url,
                "error": "Invalid token",
            },
        )
