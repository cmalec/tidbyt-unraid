"""Render Unraid metrics into a 64x32 WebP image for Tidbyt."""
import io
from PIL import Image, ImageDraw, ImageFont
from app import config

WIDTH = 64
HEIGHT = 32

COLOR_BG = (0, 0, 0)
COLOR_TEXT = (255, 255, 255)
COLOR_CPU = (0, 255, 0)
COLOR_RAM = (0, 200, 255)
COLOR_ARRAY_OK = (0, 255, 0)
COLOR_ARRAY_WARN = (255, 165, 0)
COLOR_ARRAY_ERR = (255, 0, 0)
COLOR_TEMP = (255, 255, 0)
COLOR_UPTIME = (200, 200, 200)


def _get_font(size: int):
    """Load font at requested size, fall back to default."""
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
    except Exception:
        try:
            return ImageFont.load_default()
        except Exception:
            return None


def _format_uptime(seconds: int) -> str:
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    if days > 0:
        return f"{days}d{hours}h"
    return f"{hours}h"


def _active_metrics(metrics: dict) -> list:
    """Return list of (metric_key, label, value, color) for enabled metrics."""
    items = []
    system = metrics.get("system", {})
    array = metrics.get("array", {})

    if "cpu" in config.METRICS:
        cpu = system.get("cpu", {})
        load = cpu.get("percentLoad", 0)
        items.append(("cpu", "CPU", f"{load}%", COLOR_CPU))

    if "ram" in config.METRICS:
        mem = system.get("memory", {})
        pct = mem.get("percent", 0)
        items.append(("ram", "RAM", f"{pct}%", COLOR_RAM))

    if "array" in config.METRICS:
        state = array.get("state", "UNKNOWN")
        cap = array.get("capacity", {})
        used = cap.get("used", 0)
        total = cap.get("size", 1)
        pct = int((used / total) * 100) if total else 0

        if state == "STARTED":
            color = COLOR_ARRAY_OK
        elif state == "STOPPED":
            color = COLOR_ARRAY_ERR
        else:
            color = COLOR_ARRAY_WARN
        items.append(("array", "ARR", f"{pct}%", color))

    if "temps" in config.METRICS:
        avg_temp = 0
        unit = config.TEMP_UNIT
        temp_data = system.get("temperature", {})
        if temp_data and temp_data.get("average"):
            avg_temp = int(temp_data["average"])
        else:
            disks = array.get("disks", [])
            temps = [d.get("temp", 0) for d in disks if d.get("temp", 0) > 0]
            if temps:
                avg_temp = sum(temps) // len(temps)
        if avg_temp > 0:
            if config.TEMP_UNIT == "F":
                avg_temp = int(avg_temp * 9 / 5 + 32)
                unit = "F"
            else:
                unit = "C"
            items.append(("temps", "TMP", f"{avg_temp}{unit}", COLOR_TEMP))

    if "docker" in config.METRICS:
        containers = metrics.get("docker", [])
        running = sum(1 for c in containers if c.get("state") == "running")
        total = len(containers)
        items.append(("docker", "DKR", f"{running}/{total}", COLOR_RAM))

    if "vms" in config.METRICS:
        vms = metrics.get("vms", [])
        running = sum(1 for v in vms if v.get("state") == "running")
        total = len(vms)
        items.append(("vms", "VM", f"{running}/{total}", COLOR_CPU))

    if "uptime" in config.METRICS:
        uptime_sec = system.get("uptime", 0)
        uptime_str = _format_uptime(uptime_sec)
        items.append(("uptime", "UP", uptime_str, COLOR_UPTIME))

    if "network" in config.METRICS:
        net = metrics.get("network", {})
        host = net.get("hostname", "")[:10]
        if host:
            items.append(("network", host, "", COLOR_UPTIME))

    return items[:4]


def render(metrics: dict) -> bytes:
    """Render metrics into a 64x32 WebP image using a grid layout."""
    items = _active_metrics(metrics)
    count = len(items)

    img = Image.new("RGB", (WIDTH, HEIGHT), COLOR_BG)
    draw = ImageDraw.Draw(img)

    if count == 0:
        buf = io.BytesIO()
        img.save(buf, format="WEBP", quality=80)
        return buf.getvalue()

    if count == 1:
        cells = [(0, 0, WIDTH, HEIGHT)]
        label_size, value_size = 16, 20
    elif count == 2:
        cells = [(0, 0, WIDTH // 2, HEIGHT), (WIDTH // 2, 0, WIDTH // 2, HEIGHT)]
        label_size, value_size = 10, 14
    elif count == 3:
        cells = [
            (0, 0, WIDTH, HEIGHT // 2),
            (0, HEIGHT // 2, WIDTH // 2, HEIGHT // 2),
            (WIDTH // 2, HEIGHT // 2, WIDTH // 2, HEIGHT // 2),
        ]
        label_size, value_size = 8, 10
    else:
        cells = [
            (0, 0, WIDTH // 2, HEIGHT // 2),
            (WIDTH // 2, 0, WIDTH // 2, HEIGHT // 2),
            (0, HEIGHT // 2, WIDTH // 2, HEIGHT // 2),
            (WIDTH // 2, HEIGHT // 2, WIDTH // 2, HEIGHT // 2),
        ]
        label_size, value_size = 7, 8

    label_font = _get_font(label_size)
    value_font = _get_font(value_size)

    for idx, (key, label, value, color) in enumerate(items):
        x, y, w, h = cells[idx]
        if label_font:
            label_bbox = draw.textbbox((0, 0), label, font=label_font)
            label_w = label_bbox[2] - label_bbox[0]
            label_x = x + (w - label_w) // 2
            label_y = y + 1
            draw.text((label_x, label_y), label, fill=color, font=label_font)
        if value and value_font:
            value_bbox = draw.textbbox((0, 0), value, font=value_font)
            value_w = value_bbox[2] - value_bbox[0]
            value_h = value_bbox[3] - value_bbox[1]
            value_x = x + (w - value_w) // 2
            value_y = y + h - value_h - 1
            draw.text((value_x, value_y), value, fill=COLOR_TEXT, font=value_font)

    buf = io.BytesIO()
    img.save(buf, format="WEBP", quality=80)
    return buf.getvalue()
