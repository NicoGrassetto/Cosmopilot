from __future__ import annotations


def build_resource_label(service: str, environment: str = "dev") -> str:
    """Build a normalized resource label from a service name and environment.

    :param service: The service name to include in the label.
    :param environment: The deployment environment to include in the label. Defaults to "dev".
    :return: A lowercase, hyphen-joined label in the form ``"{service}-{environment}"``.
    """
    return f"{service.strip().lower()}-{environment.strip().lower()}"
