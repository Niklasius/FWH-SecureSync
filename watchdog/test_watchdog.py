import time
import json
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

CONFIG_FILE = Path(__file__).parent / "config-test_watchdog.json"


def load_config():
    if not CONFIG_FILE.exists():
        print(f"Config-Datei nicht gefunden: {CONFIG_FILE}")
        exit(1)
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


class MeinHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if not event.is_directory:
            print(f"Datei geändert: {event.src_path}")

    def on_created(self, event):
        if not event.is_directory:
            print(f"Datei erstellt: {event.src_path}")

    def on_deleted(self, event):
        if not event.is_directory:
            print(f"Datei gelöscht: {event.src_path}")

    def on_moved(self, event):
        if not event.is_directory:
            print(f"Datei verschoben: {event.src_path} -> {event.dest_path}")


if __name__ == "__main__":
    config = load_config()
    watch_path = config["watch_path"]
    recursive = config.get("recursive", False)

    print(f"Überwache: {watch_path}  (recursive={recursive})")

    event_handler = MeinHandler()
    observer = Observer()
    observer.schedule(event_handler, path=watch_path, recursive=recursive)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
