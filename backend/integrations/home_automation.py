"""
Home Automation Integrations: MQTT and Home Assistant adapters (Phase 4)
Provides basic connectors and tool handlers to control devices and query state.
"""
from __future__ import annotations
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

try:
    import paho.mqtt.client as mqtt
except ImportError:
    mqtt = None

try:
    import requests
except ImportError:
    requests = None


class MQTTClient:
    def __init__(self, host: str = "localhost", port: int = 1883, username: Optional[str] = None, password: Optional[str] = None, tls: bool = False):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.tls = tls
        self.client = None

    def connect(self):
        if mqtt is None:
            logger.warning("paho-mqtt not installed; MQTT disabled")
            return False
        self.client = mqtt.Client()
        if self.username and self.password:
            self.client.username_pw_set(self.username, self.password)
        if self.tls:
            self.client.tls_set()
        try:
            self.client.connect(self.host, self.port, 60)
            logger.info(f"Connected to MQTT broker {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"MQTT connect failed: {e}")
            return False

    def publish(self, topic: str, payload: str, qos: int = 0, retain: bool = False) -> bool:
        if self.client is None:
            ok = self.connect()
            if not ok:
                return False
        try:
            self.client.publish(topic, payload, qos=qos, retain=retain)
            return True
        except Exception as e:
            logger.error(f"MQTT publish error: {e}")
            return False


class HomeAssistantAPI:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip('/')
        self.token = token

    def call_service(self, domain: str, service: str, data: Dict[str, Any]) -> Dict[str, Any]:
        if requests is None:
            return {"status": "error", "message": "requests not installed"}
        url = f"{self.base_url}/api/services/{domain}/{service}"
        headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
        try:
            resp = requests.post(url, headers=headers, json=data, timeout=10)
            if resp.ok:
                return {"status": "ok", "data": resp.json()}
            return {"status": "error", "code": resp.status_code, "message": resp.text}
        except Exception as e:
            logger.error(f"Home Assistant API error: {e}")
            return {"status": "error", "message": str(e)}

    def get_state(self, entity_id: str) -> Dict[str, Any]:
        if requests is None:
            return {"status": "error", "message": "requests not installed"}
        url = f"{self.base_url}/api/states/{entity_id}"
        headers = {"Authorization": f"Bearer {self.token}"}
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.ok:
                return {"status": "ok", "data": resp.json()}
            return {"status": "error", "code": resp.status_code, "message": resp.text}
        except Exception as e:
            logger.error(f"Home Assistant get_state error: {e}")
            return {"status": "error", "message": str(e)}
