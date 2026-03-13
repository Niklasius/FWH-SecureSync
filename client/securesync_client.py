import os
import time
import logging
import paramiko
from pathlib import Path
from dotenv import load_dotenv
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# --- LOGGING ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler("transfer.log"),
        logging.StreamHandler()
    ]
)

# --- LOAD .env ---
load_dotenv(dotenv_path=Path(__file__).parent / ".env")

SSH_HOST        = os.getenv("SSH_HOST")
SSH_USER        = os.getenv("SSH_USER")
SSH_KEY_NAME    = os.getenv("SSH_KEY_NAME", "github")
REMOTE_DIR      = os.getenv("REMOTE_DIR", f"/home/{SSH_USER}/uploads")
WATCH_PATH      = os.getenv("WATCH_PATH")
WATCH_RECURSIVE = os.getenv("WATCH_RECURSIVE", "false").lower() == "true"
WATCH_EXTENSIONS = [e.strip().lower() for e in os.getenv("WATCH_EXTENSIONS", "").split(",") if e.strip()]

PRIVATE_KEY_PATH = os.path.expanduser(os.path.join("~", ".ssh", SSH_KEY_NAME))


def upload_file(local_path: str):
    """Uploads a single file to the remote server via SFTP."""
    if not SSH_HOST or not SSH_USER:
        logging.error("SSH_HOST or SSH_USER missing in .env")
        return

    if not os.path.exists(PRIVATE_KEY_PATH):
        logging.error(f"Private key not found: {PRIVATE_KEY_PATH}")
        return

    file_name = Path(local_path).name
    remote_path = f"{REMOTE_DIR}/{file_name}"

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(
            hostname=SSH_HOST,
            username=SSH_USER,
            key_filename=PRIVATE_KEY_PATH,
            timeout=10
        )
        sftp = client.open_sftp()
        sftp.put(local_path, remote_path)
        sftp.close()
        logging.info(f"Uploaded: {file_name} -> {SSH_HOST}:{remote_path}")
    except Exception as e:
        logging.error(f"Upload failed for {file_name}: {e}")
    finally:
        client.close()


class SyncHandler(FileSystemEventHandler):
    def __init__(self, extensions: list):
        self.extensions = extensions  # empty = all types

    def _allowed(self, path: str) -> bool:
        if not self.extensions:
            return True
        return Path(path).suffix.lower() in self.extensions

    def on_created(self, event):
        if not event.is_directory and self._allowed(event.src_path):
            logging.info(f"New file detected: {event.src_path}")
            upload_file(event.src_path)

    def on_modified(self, event):
        if not event.is_directory and self._allowed(event.src_path):
            logging.info(f"File modified: {event.src_path}")
            upload_file(event.src_path)


if __name__ == "__main__":
    if not WATCH_PATH:
        logging.error("WATCH_PATH missing in .env")
        exit(1)

    if not os.path.isdir(WATCH_PATH):
        logging.error(f"Watch directory does not exist: {WATCH_PATH}")
        exit(1)

    ext_display = ", ".join(WATCH_EXTENSIONS) if WATCH_EXTENSIONS else "all"
    logging.info(f"Watching: {WATCH_PATH}  (recursive={WATCH_RECURSIVE})  (extensions: {ext_display})")
    logging.info(f"Uploading to: {SSH_USER}@{SSH_HOST}:{REMOTE_DIR}")

    handler = SyncHandler(extensions=WATCH_EXTENSIONS)
    observer = Observer()
    observer.schedule(handler, path=WATCH_PATH, recursive=WATCH_RECURSIVE)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Stopping observer...")
        observer.stop()
    observer.join()
    logging.info("SecureSync stopped.")
