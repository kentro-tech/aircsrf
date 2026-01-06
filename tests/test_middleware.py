import pytest
from air_csrf import CSRFConfig, CSRFMiddleware


class TestCSRFConfig:
    def test_default_values(self):
        config = CSRFConfig()
        
        assert config.cookie_name == "XSRF-TOKEN"
        assert config.header_name == "X-CSRF-Token"
        assert config.form_field == "csrf_token"
        assert config.token_length == 32
        assert config.max_age == 86400
        assert config.secure is True
        assert config.samesite == "lax"
        assert config.exempt_paths == []
        assert config.exempt_path_prefixes == ["/webhooks/"]
        assert config.exempt_methods == {"GET", "HEAD", "OPTIONS", "TRACE"}

    def test_custom_values(self):
        config = CSRFConfig(
            cookie_name="MY-TOKEN",
            header_name="X-My-Token",
            form_field="my_csrf",
            token_length=64,
            max_age=3600,
            secure=False,
            samesite="strict",
            exempt_paths=["/health", "/metrics"],
            exempt_path_prefixes=["/api/public/"],
            exempt_methods={"GET"},
        )
        
        assert config.cookie_name == "MY-TOKEN"
        assert config.header_name == "X-My-Token"
        assert config.form_field == "my_csrf"
        assert config.token_length == 64
        assert config.max_age == 3600
        assert config.secure is False
        assert config.samesite == "strict"
        assert config.exempt_paths == ["/health", "/metrics"]
        assert config.exempt_path_prefixes == ["/api/public/"]
        assert config.exempt_methods == {"GET"}


class TestCSRFMiddleware:
    def test_generate_token_length(self):
        middleware = CSRFMiddleware(app=None)
        token = middleware._generate_token()
        
        assert len(token) > 0
        assert isinstance(token, str)

    def test_should_validate_exempt_methods(self):
        from starlette.requests import Request
        from starlette.testclient import TestClient
        
        middleware = CSRFMiddleware(app=None)
        
        class MockRequest:
            method = "GET"
            url = type("URL", (), {"path": "/some-path"})()
        
        assert middleware._should_validate(MockRequest()) is False
        
        MockRequest.method = "POST"
        assert middleware._should_validate(MockRequest()) is True

    def test_should_validate_exempt_paths(self):
        config = CSRFConfig(exempt_paths=["/health"])
        middleware = CSRFMiddleware(app=None, config=config)
        
        class MockRequest:
            method = "POST"
            url = type("URL", (), {"path": "/health"})()
        
        assert middleware._should_validate(MockRequest()) is False
        
        MockRequest.url.path = "/other"
        assert middleware._should_validate(MockRequest()) is True

    def test_should_validate_exempt_prefixes(self):
        middleware = CSRFMiddleware(app=None)
        
        class MockRequest:
            method = "POST"
            url = type("URL", (), {"path": "/webhooks/stripe"})()
        
        assert middleware._should_validate(MockRequest()) is False
        
        MockRequest.url.path = "/api/users"
        assert middleware._should_validate(MockRequest()) is True

    def test_default_error_response(self):
        response = CSRFMiddleware._default_error_response("Test error")
        
        assert response.status_code == 403
        assert response.body == b"Test error"
        assert response.media_type == "text/plain"

    def test_custom_error_response(self):
        from starlette.responses import JSONResponse
        
        def custom_error(message: str):
            return JSONResponse({"error": message}, status_code=403)
        
        middleware = CSRFMiddleware(app=None, error_response=custom_error)
        response = middleware.error_response("Test error")
        
        assert response.status_code == 403
