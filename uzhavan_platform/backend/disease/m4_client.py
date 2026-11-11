"""
UZHAVAN AI — M4 Inference Client
================================
Client communicating with the persistent M4 EfficientNetV2-S inference server.
The model checkpoint is loaded once at server startup.
"""

from __future__ import annotations

import asyncio
import logging
import subprocess
import time
from pathlib import Path
from typing import Any, Dict

import httpx

logger = logging.getLogger("uzhavan.m4")

_SERVER_SCRIPT = Path("/Users/ajaikumarn/Desktop/agri/uzhavan_ml/service/m4_inference_server.py")
_ML_PYTHON = Path("/Users/ajaikumarn/Desktop/agri/.venv_ml/bin/python")
_SERVER_PROCESS: subprocess.Popen | None = None


async def is_m4_server_healthy(service_url: str = "http://127.0.0.1:8001") -> bool:
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get(f"{service_url.rstrip('/')}/health")
            if resp.status_code == 200:
                data = resp.json()
                return data.get("status") == "ok"
    except Exception:
        pass
    return False


async def ensure_m4_server_running(service_url: str = "http://127.0.0.1:8001") -> bool:
    global _SERVER_PROCESS
    if await is_m4_server_healthy(service_url):
        return True

    logger.info("M4 inference server not responding on %s. Launching...", service_url)
    try:
        _SERVER_PROCESS = subprocess.Popen(
            [str(_ML_PYTHON), str(_SERVER_SCRIPT), "8001"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        # Wait up to 5 seconds for model weights to load into memory
        for _ in range(25):
            await asyncio.sleep(0.2)
            if await is_m4_server_healthy(service_url):
                logger.info("M4 inference server successfully started and ready!")
                return True
    except Exception as exc:
        logger.error("Failed to start M4 inference server: %s", exc)

    return False


async def run_m4_inference(
    image_bytes: bytes,
    crop: str = "groundnut",
    service_url: str = "http://127.0.0.1:8001",
    timeout_s: float = 15.0,
) -> Dict[str, Any]:
    """Send image to the persistent M4 model server and return the real prediction."""
    url = f"{service_url.rstrip('/')}/predict"
    async with httpx.AsyncClient(timeout=timeout_s) as client:
        files = {"image": ("leaf.jpg", image_bytes, "image/jpeg")}
        data = {"crop": crop}
        resp = await client.post(url, files=files, data=data)
        if resp.status_code != 200:
            raise RuntimeError(f"M4 inference failed ({resp.status_code}): {resp.text}")
        return resp.json()
