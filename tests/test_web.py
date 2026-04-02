from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_landing_page_has_conversion_cta() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "Book a Demo" in response.text


def test_demo_form_submission() -> None:
    response = client.post(
        "/demo",
        data={"first_name": "Ada", "work_email": "ada@example.com", "company": "Mira"},
    )
    assert response.status_code == 200
    assert "Merci Ada" in response.text
