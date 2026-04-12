import json
from datetime import datetime

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.agents.registry import list_agents, recent_logs
from app.api.routes import pipeline
from app.integrations.manager import list_integrations

router = APIRouter()
templates = Jinja2Templates(directory="app/web/templates")

# ─── Jinja2 helpers ───────────────────────────────────────────────────────────

INTEG_COLORS = {
    "n8n":    "#ea4b71",
    "make":   "#7c3aed",
    "claude": "#d97706",
    "openai": "#10b981",
    "gemini": "#3b82f6",
    "custom": "#64748b",
}

INTEG_EMOJIS = {
    "n8n":    "⚡",
    "make":   "🔮",
    "claude": "🧠",
    "openai": "🤖",
    "gemini": "✨",
    "custom": "🔧",
}

# Pixel avatars (SVG inline, unique per integration)
PIXEL_AVATARS = {
    "n8n": """<svg width="48" height="48" viewBox="0 0 10 10" xmlns="http://www.w3.org/2000/svg" shape-rendering="crispEdges">
  <rect x="3" y="1" width="4" height="1" fill="#ea4b71"/>
  <rect x="2" y="2" width="6" height="3" fill="#ea4b71"/>
  <rect x="3" y="2" width="1" height="1" fill="#060b18"/>
  <rect x="6" y="2" width="1" height="1" fill="#060b18"/>
  <rect x="3" y="4" width="4" height="1" fill="#c83056"/>
  <rect x="1" y="5" width="8" height="3" fill="#ea4b71"/>
  <rect x="2" y="8" width="2" height="2" fill="#ea4b71"/>
  <rect x="6" y="8" width="2" height="2" fill="#ea4b71"/>
  <rect x="0" y="6" width="1" height="1" fill="#c83056"/>
  <rect x="9" y="6" width="1" height="1" fill="#c83056"/>
</svg>""",
    "make": """<svg width="48" height="48" viewBox="0 0 10 10" xmlns="http://www.w3.org/2000/svg" shape-rendering="crispEdges">
  <rect x="3" y="0" width="4" height="2" fill="#7c3aed"/>
  <rect x="2" y="2" width="6" height="1" fill="#a855f7"/>
  <rect x="1" y="3" width="8" height="3" fill="#7c3aed"/>
  <rect x="2" y="3" width="1" height="1" fill="#060b18"/>
  <rect x="7" y="3" width="1" height="1" fill="#060b18"/>
  <rect x="3" y="5" width="4" height="1" fill="#5b21b6"/>
  <rect x="2" y="6" width="6" height="2" fill="#7c3aed"/>
  <rect x="3" y="8" width="1" height="2" fill="#7c3aed"/>
  <rect x="6" y="8" width="1" height="2" fill="#7c3aed"/>
</svg>""",
    "claude": """<svg width="48" height="48" viewBox="0 0 10 10" xmlns="http://www.w3.org/2000/svg" shape-rendering="crispEdges">
  <rect x="2" y="1" width="6" height="1" fill="#d97706"/>
  <rect x="1" y="2" width="8" height="4" fill="#d97706"/>
  <rect x="2" y="3" width="1" height="1" fill="#fff7ed"/>
  <rect x="7" y="3" width="1" height="1" fill="#fff7ed"/>
  <rect x="3" y="5" width="4" height="1" fill="#92400e"/>
  <rect x="2" y="6" width="6" height="2" fill="#d97706"/>
  <rect x="0" y="3" width="1" height="2" fill="#b45309"/>
  <rect x="9" y="3" width="1" height="2" fill="#b45309"/>
  <rect x="3" y="8" width="4" height="2" fill="#d97706"/>
</svg>""",
    "openai": """<svg width="48" height="48" viewBox="0 0 10 10" xmlns="http://www.w3.org/2000/svg" shape-rendering="crispEdges">
  <rect x="3" y="0" width="4" height="2" fill="#10b981"/>
  <rect x="2" y="2" width="6" height="4" fill="#10b981"/>
  <rect x="3" y="3" width="1" height="1" fill="#064e3b"/>
  <rect x="6" y="3" width="1" height="1" fill="#064e3b"/>
  <rect x="3" y="5" width="4" height="1" fill="#059669"/>
  <rect x="1" y="6" width="8" height="2" fill="#10b981"/>
  <rect x="2" y="8" width="2" height="2" fill="#10b981"/>
  <rect x="6" y="8" width="2" height="2" fill="#10b981"/>
</svg>""",
    "gemini": """<svg width="48" height="48" viewBox="0 0 10 10" xmlns="http://www.w3.org/2000/svg" shape-rendering="crispEdges">
  <rect x="4" y="0" width="2" height="1" fill="#3b82f6"/>
  <rect x="3" y="1" width="4" height="1" fill="#3b82f6"/>
  <rect x="2" y="2" width="6" height="3" fill="#3b82f6"/>
  <rect x="3" y="3" width="1" height="1" fill="#eff6ff"/>
  <rect x="6" y="3" width="1" height="1" fill="#eff6ff"/>
  <rect x="2" y="5" width="6" height="1" fill="#1d4ed8"/>
  <rect x="3" y="6" width="4" height="2" fill="#3b82f6"/>
  <rect x="2" y="8" width="1" height="2" fill="#3b82f6"/>
  <rect x="7" y="8" width="1" height="2" fill="#3b82f6"/>
  <rect x="4" y="8" width="2" height="1" fill="#60a5fa"/>
</svg>""",
    "custom": """<svg width="48" height="48" viewBox="0 0 10 10" xmlns="http://www.w3.org/2000/svg" shape-rendering="crispEdges">
  <rect x="3" y="1" width="4" height="2" fill="#64748b"/>
  <rect x="2" y="3" width="6" height="3" fill="#64748b"/>
  <rect x="3" y="4" width="1" height="1" fill="#0f172a"/>
  <rect x="6" y="4" width="1" height="1" fill="#0f172a"/>
  <rect x="3" y="6" width="4" height="1" fill="#475569"/>
  <rect x="2" y="7" width="6" height="2" fill="#64748b"/>
  <rect x="3" y="9" width="2" height="1" fill="#64748b"/>
  <rect x="5" y="9" width="2" height="1" fill="#64748b"/>
</svg>""",
}


def _agent_avatar(integration: str, _agent_id: str) -> str:
    return PIXEL_AVATARS.get(integration, PIXEL_AVATARS["custom"])


def _integ_color(integration: str) -> str:
    return INTEG_COLORS.get(integration, "#64748b")


def _integ_emoji(integration: str) -> str:
    return INTEG_EMOJIS.get(integration, "🔧")


def _format_dt(dt: datetime | None) -> str:
    if not dt:
        return "—"
    return dt.strftime("%H:%M:%S")


def _hex_to_rgb(hex_color: str) -> str:
    """Convertit #rrggbb en 'r,g,b' pour rgba() en CSS."""
    h = hex_color.lstrip("#")
    if len(h) == 6:
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return f"{r},{g},{b}"
    return "100,100,100"


templates.env.globals["agent_avatar"] = _agent_avatar
templates.env.globals["integ_color"] = _integ_color
templates.env.globals["integ_emoji"] = _integ_emoji
templates.env.globals["format_dt"] = _format_dt
templates.env.filters["hex_to_rgb"] = _hex_to_rgb


# ─── Routes ───────────────────────────────────────────────────────────────────


@router.get("/", response_class=RedirectResponse)
async def root_redirect() -> RedirectResponse:
    """L'entrée produit redirige vers le dashboard — la landing marketing est indépendante."""
    return RedirectResponse(url="/dashboard", status_code=302)


@router.get("/dashboard", response_class=HTMLResponse)
async def reliability_dashboard(request: Request) -> HTMLResponse:
    snapshot = pipeline.metrics.snapshot()
    anomalies = pipeline.anomaly_store[-20:]
    agents = list_agents()
    running = sum(1 for a in agents if a.status.value == "running")
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "snapshot": snapshot,
            "anomalies": anomalies,
            "anomaly_rate": (
                round(snapshot.anomalies_detected / snapshot.total_events * 100, 2)
                if snapshot.total_events else 0
            ),
            "agents_total": len(agents),
            "agents_running": running,
            "logs": recent_logs(50),
        },
    )


@router.get("/agents", response_class=HTMLResponse)
async def agents_page(request: Request) -> HTMLResponse:
    agents = list_agents()
    running = sum(1 for a in agents if a.status.value == "running")
    errors = sum(1 for a in agents if a.status.value == "error")
    return templates.TemplateResponse(
        request,
        "agents.html",
        {
            "agents": agents,
            "agents_total": len(agents),
            "agents_running": running,
            "agents_error": errors,
            "agents_json": json.dumps([a.model_dump(mode="json") for a in agents]),
        },
    )


@router.get("/integrations", response_class=HTMLResponse)
async def integrations_page(request: Request) -> HTMLResponse:
    integrations = list_integrations()
    connected = sum(1 for i in integrations if i.status.value == "connected")
    return templates.TemplateResponse(
        request,
        "integrations.html",
        {
            "integrations": integrations,
            "connected_count": connected,
        },
    )


@router.get("/demo", response_class=HTMLResponse)
async def demo_request(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "demo.html", {"submitted": False})


@router.post("/demo", response_class=HTMLResponse)
async def submit_demo_request(request: Request) -> HTMLResponse:
    form = await request.form()
    return templates.TemplateResponse(
        request,
        "demo.html",
        {
            "submitted": True,
            "first_name": form.get("first_name", ""),
            "company": form.get("company", ""),
        },
    )
