"""Pydantic schemas for system health and diagnostics."""

from typing import Any, Dict
from pydantic import BaseModel, Field


class ComponentStatus(BaseModel):
    """Health status of an individual system component."""
    status: str = Field(description="ok, degraded, or error")
    details: Dict[str, Any] = Field(default_factory=dict)


class HealthResponse(BaseModel):
    """Overall system health report."""
    app_name: str
    status: str = Field(description="healthy, degraded, or unhealthy")
    version: str
    components: Dict[str, ComponentStatus]
