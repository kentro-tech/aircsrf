"""
Minimal demo showing CSRF protection use cases.

Run with: just demo
Then visit: http://localhost:8000
"""

import air
from starlette.responses import PlainTextResponse
from starlette.staticfiles import StaticFiles

from air_csrf import CSRFMiddleware, CSRFConfig, get_form


app = air.Air()

# secure=False allows cookies over HTTP (required for localhost dev)
# In production, use secure=True (the default) for HTTPS-only cookies
app.add_middleware(CSRFMiddleware, config=CSRFConfig(secure=False))
app.mount("/static", StaticFiles(directory="static"), name="static")


def page(*children) -> air.Html:
    """Wrap content in mvpcss layout with CSRF script."""
    return air.layouts.mvpcss(
        air.Title("CSRF Demo"),
        air.Script(src="/static/csrf.js", type_="module"),
        air.Style("* { text-align: left; margin-left: 0; margin-right: auto; }"),
        *children,
    )


@app.get("/")
async def index():
    return page(
        air.H1("CSRF Protection Demo"),
        air.Section(
            air.H2("1. Traditional Form"),
            air.P("Hidden field populated by csrf.js from cookie."),
            air.Form(
                air.Input(type_="hidden", name="csrf_token"),
                air.Input(type_="text", name="message", placeholder="Enter a message"),
                air.Button("Submit", type_="submit"),
                method="post",
                action="/form-submit",
            ),
        ),
        air.Section(
            air.H2("2. htmx Request"),
            air.P("Token sent via header automatically by csrf.js."),
            air.Button(
                "htmx POST",
                hx_post="/htmx-action",
                hx_target="#htmx-result",
                hx_swap="innerHTML",
            ),
            air.Div(id_="htmx-result"),
        ),
        air.Section(
            air.H2("3. Fetch API"),
            air.P("Token read from cookie and sent in header."),
            air.Button("Fetch POST", id_="fetch-btn"),
            air.Div(id_="fetch-result"),
            air.Script("""
                import { getCsrfToken } from '/static/csrf.js';
                document.getElementById('fetch-btn').onclick = async () => {
                    const res = await fetch('/api-action', {
                        method: 'POST',
                        headers: { 'X-CSRF-Token': getCsrfToken() },
                    });
                    document.getElementById('fetch-result').textContent = 
                        res.status + ': ' + await res.text();
                };
            """, type_="module"),
        ),
        air.Section(
            air.H2("4. Missing Token (Error)"),
            air.P("Demonstrates 403 when token is missing."),
            air.Button("POST without Token", id_="error-btn"),
            air.Div(id_="error-result"),
            air.Script("""
                document.getElementById('error-btn').onclick = async () => {
                    const res = await fetch('/api-action', { method: 'POST' });
                    document.getElementById('error-result').textContent = 
                        res.status + ': ' + await res.text();
                };
            """, type_="module"),
        ),
    )


@app.post("/form-submit")
async def form_submit(request: air.Request):
    form = await get_form(request)
    message = form.get("message", "")
    return air.P(f"Form submitted! Message: {message}")


@app.post("/htmx-action")
async def htmx_action():
    return air.P("htmx action successful!")


@app.post("/api-action")
async def api_action():
    return PlainTextResponse("API action successful!")


if __name__ == "__main__":
    import uvicorn

    print("Demo running at http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
