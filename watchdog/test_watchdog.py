import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

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

event_handler = MeinHandler()
observer = Observer()
observer.schedule(event_handler, path='.', recursive=False)
observer.start()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    observer.stop()
observer.join()