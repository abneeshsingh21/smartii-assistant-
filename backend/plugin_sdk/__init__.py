"""
Smartii Plugin SDK
Defines the base plugin interface and permission/manifest schemas for third-party extensions.
"""
from __future__ import annotations
from typing import Callable, Dict, Any, Optional, List
from dataclasses import dataclass, field


@dataclass
class ToolSpec:
    name: str
    description: str
    params_schema: Optional[Dict[str, Any]] = None
    permissions: Optional[List[str]] = None


class BasePlugin:
    """
    Base class for Smartii plugins.
    Plugins must implement `register(self, register_tool: Callable[[str, Callable, str, Optional[Dict], Optional[List[str]]], None])`.
    """

    def __init__(self, manifest: Dict[str, Any]):
        self.manifest = manifest

    def register(self, register_tool: Callable[[str, Callable[[Dict[str, Any], Dict[str, Any]], Any], str, Optional[Dict[str, Any]], Optional[List[str]]], None]):
        raise NotImplementedError("Plugins must implement register()")


# Manifest schema (informal for now)
# {
#   "name": "string",
#   "version": "string",
#   "description": "string",
#   "author": "string",
#   "permissions": ["device.control", "web", ...],
#   "tools": [
#       {"name": "device.control.light", "description": "Control lights", "params_schema": {...}}
#   ]
# }
