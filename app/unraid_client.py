"""Client to fetch system metrics from Unraid via the official GraphQL API."""
from datetime import datetime, timezone
import requests
from app import config


def _parse_uptime(uptime_str: str) -> int:
    """Convert ISO boot-time timestamp to elapsed seconds."""
    if not uptime_str:
        return 0
    try:
        boot_time = datetime.fromisoformat(uptime_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        return int((now - boot_time).total_seconds())
    except Exception:
        return 0


def _graphql_query(query: str) -> dict:
    """Execute a GraphQL query against the Unraid API."""
    resp = requests.post(
        f"{config.UNRAID_URL}/graphql",
        json={"query": query},
        headers={"x-api-key": config.UNRAID_API_KEY, "Content-Type": "application/json"},
        timeout=30,
        verify=False,  # Unraid uses self-signed certificates by default
    )
    resp.raise_for_status()
    data = resp.json()
    if "errors" in data:
        raise RuntimeError(data["errors"])
    return data.get("data", {})


def get_system_info() -> dict:
    """Return CPU, memory, uptime, and hostname from live metrics + info."""
    # Fetch live metrics (CPU %, RAM %) and static info (uptime, hostname)
    q = """
    {
      metrics {
        cpu { percentTotal }
        memory { total used free percentTotal }
        temperature {
          summary { average }
          sensors { name current { value unit } }
        }
      }
      info {
        os { hostname uptime }
        cpu { model cores }
      }
    }
    """
    data = _graphql_query(q)
    metrics = data.get("metrics", {})
    info = data.get("info", {})

    cpu_metrics = metrics.get("cpu", {})
    mem_metrics = metrics.get("memory", {})
    temp_metrics = metrics.get("temperature", {})
    cpu_info = info.get("cpu", {})
    os_info = info.get("os", {})

    # Temperature: prefer average from sensors, fall back to 0
    avg_temp = 0
    temp_summary = temp_metrics.get("summary", {})
    if temp_summary and temp_summary.get("average") is not None:
        avg_temp = int(temp_summary["average"])

    return {
        "cpu": {
            "model": cpu_info.get("model"),
            "cores": cpu_info.get("cores"),
            "percentLoad": int(cpu_metrics.get("percentTotal", 0)),
        },
        "memory": {
            "total": mem_metrics.get("total", 0),
            "used": mem_metrics.get("used", 0),
            "free": mem_metrics.get("free", 0),
            "percent": int(mem_metrics.get("percentTotal", 0)),
        },
        "temperature": {
            "average": avg_temp,
            "sensors": [
                {
                    "name": s.get("name"),
                    "value": s.get("current", {}).get("value", 0),
                    "unit": s.get("current", {}).get("unit", "C"),
                }
                for s in temp_metrics.get("sensors", [])
            ],
        },
        "uptime": _parse_uptime(os_info.get("uptime", "")),
        "hostname": os_info.get("hostname", ""),
    }


def get_array_status() -> dict:
    """Return array state and disk usage."""
    q = """
    {
      array {
        state
        capacity { kilobytes { free used total } }
        disks { name device size status temp fsType isSpinning }
        parities { name device size status temp numErrors }
        parityCheckStatus { status progress errors speed running paused }
      }
    }
    """
    data = _graphql_query(q)
    array = data.get("array", {})
    capacity = array.get("capacity", {}).get("kilobytes", {})
    return {
        "state": array.get("state"),
        "capacity": {
            "size": int(capacity.get("total", 0)) if capacity.get("total") else 0,
            "used": int(capacity.get("used", 0)) if capacity.get("used") else 0,
            "free": int(capacity.get("free", 0)) if capacity.get("free") else 0,
        },
        "disks": array.get("disks", []),
        "parities": array.get("parities", []),
        "parityCheck": array.get("parityCheckStatus", {}),
    }


def get_docker_containers() -> list:
    """Return list of Docker containers and their states."""
    q = """
    {
      docker {
        containers { id names image state status autoStart isUpdateAvailable }
      }
    }
    """
    data = _graphql_query(q)
    containers = []
    for c in data.get("docker", {}).get("containers", []):
        containers.append({
            "id": c.get("id"),
            "name": c.get("names", [""])[0].lstrip("/") if c.get("names") else "",
            "image": c.get("image"),
            "state": c.get("state", "").lower(),
            "status": c.get("status"),
            "autoStart": c.get("autoStart", False),
            "isUpdateAvailable": c.get("isUpdateAvailable", False),
        })
    return containers


def get_vms() -> list:
    """Return list of VMs and their states."""
    q = """
    {
      vms {
        domains { id name state uuid }
      }
    }
    """
    data = _graphql_query(q)
    vms = []
    for vm in data.get("vms", {}).get("domains", []):
        vms.append({
            "id": vm.get("id"),
            "name": vm.get("name"),
            "state": vm.get("state", "").lower(),
            "uuid": vm.get("uuid"),
        })
    return vms


def get_network_info() -> dict:
    """Return network interface info."""
    q = """
    {
      info {
        os { hostname }
        primaryNetwork { name ipAddress macAddress }
      }
    }
    """
    data = _graphql_query(q)
    info_data = data.get("info", {})
    return {
        "hostname": info_data.get("os", {}).get("hostname"),
        "interface": info_data.get("primaryNetwork", {}),
    }


def get_all_metrics() -> dict:
    """Fetch all enabled metrics."""
    metrics = {}
    if "cpu" in config.METRICS or "ram" in config.METRICS or "uptime" in config.METRICS or "temps" in config.METRICS:
        metrics["system"] = get_system_info()
    if "array" in config.METRICS:
        metrics["array"] = get_array_status()
    if "docker" in config.METRICS:
        metrics["docker"] = get_docker_containers()
    if "vms" in config.METRICS:
        metrics["vms"] = get_vms()
    if "network" in config.METRICS:
        metrics["network"] = get_network_info()
    return metrics
