# air-csrf

CSRF protection for AIR/FastAPI/Starlette using the double-submit cookie pattern.

## Install

```bash
pip install air-csrf
```

## Quick Start

```python
from fastapi import FastAPI
from air_csrf import CSRFMiddleware

app = FastAPI()
app.add_middleware(CSRFMiddleware)
```

The middleware:
1. Sets an `XSRF-TOKEN` cookie on GET requests
2. Validates the token on POST/PUT/PATCH/DELETE
3. Accepts tokens via `X-CSRF-Token` header or `csrf_token` form field

## Configuration

```python
from air_csrf import CSRFMiddleware, CSRFConfig

config = CSRFConfig(
    cookie_name="XSRF-TOKEN",
    header_name="X-CSRF-Token",
    form_field="csrf_token",
    token_length=32,
    max_age=86400,
    secure=True,
    samesite="lax",
    exempt_paths=["/health"],
    exempt_path_prefixes=["/webhooks/"],
)

app.add_middleware(CSRFMiddleware, config=config)
```

| Option | Default | Description |
|--------|---------|-------------|
| `cookie_name` | `XSRF-TOKEN` | Cookie storing the token |
| `header_name` | `X-CSRF-Token` | Header for token submission |
| `form_field` | `csrf_token` | Form field for token submission |
| `token_length` | `32` | Token length in bytes |
| `max_age` | `86400` | Cookie lifetime in seconds (24h) |
| `secure` | `True` | HTTPS-only cookie. Set `False` for localhost |
| `samesite` | `lax` | Cookie SameSite attribute |
| `exempt_paths` | `[]` | Exact paths to skip validation |
| `exempt_path_prefixes` | `["/webhooks/"]` | Path prefixes to skip |
| `exempt_methods` | `GET, HEAD, OPTIONS, TRACE` | HTTP methods to skip |

## Custom Error Response

```python
from starlette.responses import JSONResponse

def custom_error(message: str):
    return JSONResponse({"error": message}, status_code=403)

app.add_middleware(CSRFMiddleware, error_response=custom_error)
```

## Form Data

Use `get_form()` instead of `request.form()`:

```python
from air_csrf import get_form

@app.post("/submit")
async def submit(request: Request):
    form = await get_form(request)
    return {"message": form.get("message")}
```

The middleware consumes the body to validate the token. `get_form()` returns the cached data.

## Client-Side

### Script Setup

Include the provided `csrf.js`. It auto-initializes on page load:

```html
<script type="module" src="/static/csrf.js"></script>
```

This handles:
- Populating hidden `csrf_token` fields in forms
- Adding `X-CSRF-Token` header to htmx requests

### Forms

```html
<form method="post" action="/submit">
    <input type="hidden" name="csrf_token">
    <button type="submit">Submit</button>
</form>
```

### htmx

Works automatically with `csrf.js`:

```html
<button hx-post="/action">Click</button>
```

### Fetch

```javascript
import { getCsrfToken } from '/static/csrf.js';

fetch('/api/action', {
    method: 'POST',
    headers: { 'X-CSRF-Token': getCsrfToken() },
    body: JSON.stringify({ data: 'value' }),
});
```

## Jinja2

```python
from air_csrf import csrf_jinja2_context_processor

@app.get("/form")
def form_page(request: Request):
    return templates.TemplateResponse(
        "form.html",
        {"request": request, **csrf_jinja2_context_processor(request)}
    )
```

Template:

```html
<input type="hidden" name="csrf_token" value="{{ csrf_token }}">
```

## How It Works

1. First request: middleware generates a random token, stores it in `XSRF-TOKEN` cookie
2. Cookie is readable by JavaScript (`httponly=False`)
3. Client submits the token via header or form field
4. Middleware compares values using constant-time comparison
5. Mismatch returns 403

## Security

- Use `secure=True` in production (HTTPS only)
- `SameSite=Lax` default protects against cross-site attacks
- Webhooks exempt by default (use signature auth instead)
- Tokens use Python's `secrets` module

## License

MIT
