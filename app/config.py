"""Configuration loaded from environment variables."""
import os

UNRAID_URL = os.getenv("UNRAID_URL", "").rstrip("/")
UNRAID_API_KEY = os.getenv("UNRAID_API_KEY", "")
TIDBYT_DEVICE_ID = os.getenv("TIDBYT_DEVICE_ID", "")
TIDBYT_API_KEY = os.getenv("TIDBYT_API_KEY", "")
_update_interval_raw = os.getenv("UPDATE_INTERVAL", "3600")
try:
    UPDATE_INTERVAL = int(_update_interval_raw)
except ValueError:
    raise ValueError(f"UPDATE_INTERVAL must be an integer, got: {_update_interval_raw!r}")
METRICS = [m.strip().lower() for m in os.getenv("METRICS", "cpu,ram,array,uptime").split(",")]
TEMP_UNIT = os.getenv("TEMP_UNIT", "F").upper()

# Validate
if not UNRAID_URL:
    raise ValueError("UNRAID_URL environment variable is required")
if not UNRAID_API_KEY:
    raise ValueError("UNRAID_API_KEY environment variable is required")
if not TIDBYT_DEVICE_ID:
    raise ValueError("TIDBYT_DEVICE_ID environment variable is required")
if not TIDBYT_API_KEY:
    raise ValueError("TIDBYT_API_KEY environment variable is required")
