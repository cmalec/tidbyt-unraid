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
    """Return list of (metric_key, label, value, color, bar_pct) for enabled metrics."""
    items = []
    system = metrics.get("system", {})
    array = metrics.get("array", {})

    if "cpu" in config.METRICS:
        cpu = system.get("cpu", {})
        load = cpu.get("percentLoad", 0)
        items.append(("cpu", "CPU", f"{load}%", COLOR_CPU, load))

    if "ram" in config.METRICS:
        mem = system.get("memory", {})
        pct = mem.get("percent", 0)
        items.append(("ram", "RAM", f"{pct}%", COLOR_RAM, pct))

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
        items.append(("array", "ARR", f"{pct}%", color, pct))

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
            items.append(("temps", "TMP", f"{avg_temp}{unit}", COLOR_TEMP, None))

    if "docker" in config.METRICS:
        containers = metrics.get("docker", [])
        running = sum(1 for c in containers if c.get("state") == "running")
        total = len(containers)
        items.append(("docker", "DKR", f"{running}/{total}", COLOR_RAM, None))

    if "vms" in config.METRICS:
        vms = metrics.get("vms", [])
        running = sum(1 for v in vms if v.get("state") == "running")
        total = len(vms)
        items.append(("vms", "VM", f"{running}/{total}", COLOR_CPU, None))

    if "uptime" in config.METRICS:
        uptime_sec = system.get("uptime", 0)
        uptime_str = _format_uptime(uptime_sec)
        items.append(("uptime", "UP", uptime_str, COLOR_UPTIME, None))

    if "network" in config.METRICS:
        net = metrics.get("network", {})
        host = net.get("hostname", "")[:10]
        if host:
            items.append(("network", host, "", COLOR_UPTIME, None))

    return items


def render(metrics: dict) -> bytes:
    """Render metrics into a 64x32 WebP image, dynamically sized to fit all enabled metrics."""
    items = _active_metrics(metrics)
    count = len(items)

    if count == 0:
        # Nothing to show
        img = Image.new("RGB", (WIDTH, HEIGHT), COLOR_BG)
        buf = io.BytesIO()
        img.save(buf, format="WEBP", quality=80)
        return buf.getvalue()

    # Dynamic sizing based on item count
    if count == 1:
        label_size, value_size = 10, 14
        label_offset = 2
        value_offset = 28
        bar_y_offset = 4
        bar_height = 6
    elif count <= 2:
        label_size, value_size = 8, 10
        label_offset = 2
        value_offset = 24
        bar_y_offset = 3
        bar_height = 5
    elif count <= 3:
        label_size, value_size = 7, 8
        label_offset = 2
        value_offset = 22
        bar_y_offset = 3
        bar_height = 4
    elif count <= 5:
        label_size, value_size = 5, 6
        label_offset = 1
        value_offset = 18
        bar_y_offset = 2
        bar_height = 3
    else:
        label_size, value_size = 4, 5
        label_offset = 0
        value_offset = 16
        bar_y_offset = 1
        bar_height = 2

    line_height = HEIGHT // count

    label_font = _get_font(label_size)
    value_font = _get_font(value_size)

    img = Image.new("RGB", (WIDTH, HEIGHT), COLOR_BG)
    draw = ImageDraw.Draw(img)

    for idx, (key, label, value, color, bar_pct) in enumerate(items):
        y = idx * line_height

        # Draw label
        draw.text((label_offset, y), label, fill=color, font=label_font)

        # Draw value (if any)
        if value:
            draw.text((value_offset, y), value, fill=COLOR_TEXT, font=value_font)

        # Draw progress bar (if percentage provided)
        if bar_pct is not None:
            bar_w = int((bar_pct / 100) * 20)
            bar_y = y + bar_y_offset
            draw.rectangle(
                [44, bar_y, 44 + bar_w, bar_y + bar_height],
                fill=color
            )

    buf = io.BytesIO()
    img.save(buf, format="WEBP", quality=80)
    return buf.getvalue()
