"""Main scheduler: fetch Unraid metrics and push to Tidbyt on interval."""
import time
import traceback
from app import config
from app.unraid_client import get_all_metrics
from app.renderer import render
from app.tidbyt_client import push_image


def tick():
    """Single update cycle."""
    print("Fetching Unraid metrics...")
    metrics = get_all_metrics()

    print("Rendering image...")
    image = render(metrics)

    print("Pushing to Tidbyt...")
    result = push_image(image)
    print(f"Push result: {result}")


def main():
    print("=" * 50)
    print("Tidbyt Unraid Monitor")
    print("=" * 50)
    print(f"Unraid URL: {config.UNRAID_URL}")
    print(f"Tidbyt Device: {config.TIDBYT_DEVICE_ID}")
    print(f"Update interval: {config.UPDATE_INTERVAL}s")
    print(f"Metrics: {', '.join(config.METRICS)}")
    print("=" * 50)

    while True:
        try:
            tick()
        except Exception as e:
            print(f"Error during update: {e}")
            traceback.print_exc()

        print(f"Sleeping {config.UPDATE_INTERVAL}s...")
        time.sleep(config.UPDATE_INTERVAL)


if __name__ == "__main__":
    main()
