from dataclasses import dataclass, field


@dataclass
class CSRFConfig:
    """Configuration for CSRF middleware."""
    
    cookie_name: str = "XSRF-TOKEN"
    header_name: str = "X-CSRF-Token"
    form_field: str = "csrf_token"
    token_length: int = 32
    max_age: int = 86400
    secure: bool = True
    samesite: str = "lax"
    exempt_paths: list[str] = field(default_factory=list)
    exempt_path_prefixes: list[str] = field(default_factory=lambda: ["/webhooks/"])
    exempt_methods: set[str] = field(default_factory=lambda: {"GET", "HEAD", "OPTIONS", "TRACE"})
