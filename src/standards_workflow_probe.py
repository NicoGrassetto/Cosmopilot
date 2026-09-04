from __future__ import annotations


def build_resource_label(service: str, environment: str = "dev") -> str:
    return f"{service.strip().lower()}-{environment.strip().lower()}"