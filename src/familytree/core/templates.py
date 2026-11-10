"""Jinja2 templates configuration."""

from __future__ import annotations

from pathlib import Path

from starlette.requests import Request
from starlette.responses import HTMLResponse


def get_templates_dir() -> Path:
    """Get templates directory path."""
    return Path(__file__).resolve().parent.parent / "templates"


# Import jinja2 and create environment
import jinja2


def _create_env() -> jinja2.Environment:
    """Create a fresh Jinja2 environment for each request."""
    templates_dir = get_templates_dir()
    print(f"Creating Jinja2 env with templates from: {templates_dir} (exists: {templates_dir.exists()})")
    return jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(templates_dir)),
        autoescape=False,
        enable_async=False,
        cache_size=0,  # Disable template caching
    )


def template_response(template: str, context: dict, request: Request | None = None) -> HTMLResponse:
    """Render template without using Starlette's caching mechanism."""
    _env = _create_env()
    tmpl = _env.get_template(template)
    if request is not None:
        context["request"] = request
    html = tmpl.render(**context)
    return HTMLResponse(content=html)
