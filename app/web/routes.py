from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.api.routes import pipeline

router = APIRouter()
templates = Jinja2Templates(directory="app/web/templates")


@router.get("/", response_class=HTMLResponse)
async def landing_page(request: Request) -> HTMLResponse:
    snapshot = pipeline.metrics.snapshot()
    return templates.TemplateResponse(
        request,
        "landing.html",
        {
            "product_name": "Mira",
            "hero_title": "Data & AI Reliability for E-commerce Agents",
            "hero_subtitle": (
                "Observe prompts, predictions and recommendations with a conversion-first UX "
                "and instant anomaly triage."
            ),
            "cta_primary": "Book a Demo",
            "cta_secondary": "See Product Tour",
            "metrics": snapshot,
        },
    )


@router.get("/tour", response_class=HTMLResponse)
async def product_tour(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "tour.html",
        {
            "steps": [
                {
                    "title": "Connect",
                    "description": "Instrument agents in 5 minutes with the Python SDK.",
                },
                {
                    "title": "Observe",
                    "description": "Track event quality and drift in one data reliability cockpit.",
                },
                {
                    "title": "Act",
                    "description": "Get routed Slack alerts and investigate anomalies instantly.",
                },
            ]
        },
    )


@router.get("/demo", response_class=HTMLResponse)
async def demo_request(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "demo.html", {"submitted": False})


@router.post("/demo", response_class=HTMLResponse)
async def submit_demo_request(request: Request) -> HTMLResponse:
    form = await request.form()
    first_name = form.get("first_name", "")
    company = form.get("company", "")
    return templates.TemplateResponse(
        request,
        "demo.html",
        {
            "submitted": True,
            "first_name": first_name,
            "company": company,
        },
    )


@router.get("/dashboard", response_class=HTMLResponse)
async def reliability_dashboard(request: Request) -> HTMLResponse:
    snapshot = pipeline.metrics.snapshot()
    anomalies = pipeline.anomaly_store[-10:]
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "snapshot": snapshot,
            "anomalies": anomalies,
            "anomaly_rate": (
                round(snapshot.anomalies_detected / snapshot.total_events * 100, 2)
                if snapshot.total_events
                else 0
            ),
        },
    )
