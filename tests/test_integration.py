import pytest
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from air_csrf import CSRFConfig, CSRFMiddleware


def create_app(config: CSRFConfig | None = None):
    async def index(request):
        return PlainTextResponse("Hello")

    async def submit(request):
        return PlainTextResponse("Submitted")

    async def webhook(request):
        return PlainTextResponse("Webhook received")

    app = Starlette(
        routes=[
            Route("/", index),
            Route("/submit", submit, methods=["POST"]),
            Route("/webhooks/stripe", webhook, methods=["POST"]),
        ]
    )
    app.add_middleware(CSRFMiddleware, config=config)
    return app


class TestCSRFCookieSetOnGet:
    def test_csrf_cookie_set_on_get(self):
        app = create_app(CSRFConfig(secure=False))
        client = TestClient(app)
        
        response = client.get("/")
        
        assert response.status_code == 200
        assert "XSRF-TOKEN" in response.cookies

    def test_csrf_cookie_not_reset_on_subsequent_get(self):
        app = create_app(CSRFConfig(secure=False))
        client = TestClient(app)
        
        response1 = client.get("/")
        token1 = response1.cookies.get("XSRF-TOKEN")
        
        response2 = client.get("/")
        token2 = response2.cookies.get("XSRF-TOKEN")
        
        assert token1 is not None
        assert "XSRF-TOKEN" not in response2.cookies or token2 is None


class TestCSRFValidation:
    def test_post_without_token_fails(self):
        app = create_app(CSRFConfig(secure=False))
        client = TestClient(app)
        
        response = client.post("/submit")
        
        assert response.status_code == 403
        assert "CSRF" in response.text

    def test_post_without_cookie_fails(self):
        app = create_app(CSRFConfig(secure=False))
        client = TestClient(app, cookies={})
        
        response = client.post(
            "/submit",
            headers={"X-CSRF-Token": "fake-token"},
        )
        
        assert response.status_code == 403

    def test_post_with_header_token_succeeds(self):
        app = create_app(CSRFConfig(secure=False))
        client = TestClient(app)
        
        get_response = client.get("/")
        token = get_response.cookies.get("XSRF-TOKEN")
        
        response = client.post(
            "/submit",
            headers={"X-CSRF-Token": token},
        )
        
        assert response.status_code == 200
        assert response.text == "Submitted"

    def test_post_with_form_token_succeeds(self):
        app = create_app(CSRFConfig(secure=False))
        client = TestClient(app)
        
        get_response = client.get("/")
        token = get_response.cookies.get("XSRF-TOKEN")
        
        response = client.post(
            "/submit",
            data={"csrf_token": token, "other_field": "value"},
        )
        
        assert response.status_code == 200
        assert response.text == "Submitted"

    def test_mismatched_token_fails(self):
        app = create_app(CSRFConfig(secure=False))
        client = TestClient(app)
        
        client.get("/")
        
        response = client.post(
            "/submit",
            headers={"X-CSRF-Token": "wrong-token"},
        )
        
        assert response.status_code == 403
        assert "mismatch" in response.text.lower()


class TestExemptPaths:
    def test_webhook_exempt(self):
        app = create_app(CSRFConfig(secure=False))
        client = TestClient(app)
        
        response = client.post("/webhooks/stripe")
        
        assert response.status_code == 200
        assert response.text == "Webhook received"

    def test_custom_exempt_path(self):
        config = CSRFConfig(secure=False, exempt_paths=["/submit"])
        app = create_app(config)
        client = TestClient(app)
        
        response = client.post("/submit")
        
        assert response.status_code == 200

    def test_custom_exempt_prefix(self):
        config = CSRFConfig(
            secure=False,
            exempt_path_prefixes=["/webhooks/", "/api/public/"],
        )
        app = create_app(config)
        client = TestClient(app)
        
        response = client.post("/webhooks/stripe")
        assert response.status_code == 200


class TestCustomConfig:
    def test_custom_cookie_name(self):
        config = CSRFConfig(secure=False, cookie_name="MY-TOKEN")
        app = create_app(config)
        client = TestClient(app)
        
        response = client.get("/")
        
        assert "MY-TOKEN" in response.cookies
        assert "XSRF-TOKEN" not in response.cookies

    def test_custom_header_name(self):
        config = CSRFConfig(secure=False, header_name="X-My-Token")
        app = create_app(config)
        client = TestClient(app)
        
        get_response = client.get("/")
        token = get_response.cookies.get("XSRF-TOKEN")
        
        response = client.post(
            "/submit",
            headers={"X-My-Token": token},
        )
        
        assert response.status_code == 200

    def test_custom_form_field(self):
        config = CSRFConfig(secure=False, form_field="my_csrf_token")
        app = create_app(config)
        client = TestClient(app)
        
        get_response = client.get("/")
        token = get_response.cookies.get("XSRF-TOKEN")
        
        response = client.post(
            "/submit",
            data={"my_csrf_token": token},
        )
        
        assert response.status_code == 200
