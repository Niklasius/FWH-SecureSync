#   ---   watchdog test code   ---   #


import time
import json
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# config file path and name
CONFIG_FILE = Path(__file__).parent / "config-test_watchdog.json"

# load config file
def load_config():
    if not CONFIG_FILE.exists():
        print(f"Config-Datei nicht gefunden: {CONFIG_FILE}")
        exit(1)
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# watchdog event handler
class MeinHandler(FileSystemEventHandler):
    def __init__(self, extensions):
        self.extensions = [ext.lower() for ext in extensions]  # z.B. [".txt", ".pdf"]

    def _erlaubt(self, path):
        # leere Liste = alle Dateitypen erlaubt
        if not self.extensions:
            return True
        return Path(path).suffix.lower() in self.extensions

    def on_modified(self, event):
        if not event.is_directory and self._erlaubt(event.src_path):
            print(f"Datei geändert: {event.src_path}")

    def on_created(self, event):
        if not event.is_directory and self._erlaubt(event.src_path):
            print(f"Datei erstellt: {event.src_path}")

    def on_deleted(self, event):
        if not event.is_directory and self._erlaubt(event.src_path):
            print(f"Datei gelöscht: {event.src_path}")

    def on_moved(self, event):
        if not event.is_directory and self._erlaubt(event.src_path):
            print(f"Datei verschoben: {event.src_path} -> {event.dest_path}")


#   main code   #
if __name__ == "__main__":
    config = load_config()                          # import config file into config
    watch_path = config["watch_path"]               # load watch path from config
    watch_subfolder = config["recursive"]           # load recursive setting from config
    extensions = config.get("extensions", [])       # load file extensions from config (empty = all)

    if extensions:
        print(f"Überwache: {watch_path}  (recursive={watch_subfolder})  (Dateitypen: {', '.join(extensions)})")
    else:
        print(f"Überwache: {watch_path}  (recursive={watch_subfolder})  (Dateitypen: alle)")

    event_handler = MeinHandler(extensions=extensions)
    observer = Observer()
    observer.schedule(event_handler, path=watch_path, recursive=watch_subfolder)    # watchdog config
    observer.start()                                                                # start watchdog

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:

        observer.stop()     # stop watchdog
    observer.join()
