"""Client to push rendered images to a Tidbyt device."""
import base64
import io
import requests
from app import config


TIDBYT_API_BASE = "https://api.tidbyt.com/v0"


def push_image(image_bytes: bytes, installation_id: str = "unraid") -> dict:
    """Push a WebP image to the Tidbyt device.

    Args:
        image_bytes: Raw WebP image data (64x32).
        installation_id: Unique ID for this app installation on the device.

    Returns:
        JSON response from Tidbyt API.
    """
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    payload = {
        "deviceID": config.TIDBYT_DEVICE_ID,
        "image": b64,
        "installationID": installation_id,
        "background": False,
    }
    resp = requests.post(
        f"{TIDBYT_API_BASE}/devices/{config.TIDBYT_DEVICE_ID}/push",
        json=payload,
        headers={"Authorization": f"Bearer {config.TIDBYT_API_KEY}"},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()
