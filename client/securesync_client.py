import os
import sys
import time
import logging
import getpass
import paramiko
from pathlib import Path
from dotenv import load_dotenv, set_key
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

ENV_PATH = Path(__file__).parent / ".env"
KEY_DIR = Path.home() / ".ssh"
KEY_FILENAME = "securesync_key"
PRIVATE_KEY_PATH = KEY_DIR / KEY_FILENAME


def load_env() -> dict | None:
    """Lädt die .env und gibt die Werte als Dict zurück. None wenn unvollständig."""
    load_dotenv(dotenv_path=ENV_PATH)
    host = os.getenv("SSH_HOST")
    user = os.getenv("SSH_USER")
    watch_path = os.getenv("WATCH_PATH")
    if not host or not user or not watch_path:
        return None
    return {
        "host": host,
        "port": int(os.getenv("SSH_PORT", "22")),
        "user": user,
        "remote_dir": os.getenv("REMOTE_DIR", f"/home/{user}/uploads"),
        "watch_path": watch_path,
        "recursive": os.getenv("WATCH_RECURSIVE", "false").lower() == "true",
        "extensions": [
            e.strip().lower()
            for e in os.getenv("WATCH_EXTENSIONS", "").split(",")
            if e.strip()
        ],
        "key_path": Path(os.getenv("SSH_KEY_PATH", str(PRIVATE_KEY_PATH))),
    }


def save_env(cfg: dict):
    """Schreibt alle Einstellungen in die .env-Datei."""
    ENV_PATH.touch(exist_ok=True)
    set_key(str(ENV_PATH), "SSH_HOST", cfg["host"])
    set_key(str(ENV_PATH), "SSH_PORT", str(cfg["port"]))
    set_key(str(ENV_PATH), "SSH_USER", cfg["user"])
    set_key(str(ENV_PATH), "REMOTE_DIR", cfg["remote_dir"])
    set_key(str(ENV_PATH), "WATCH_PATH", cfg["watch_path"])
    set_key(str(ENV_PATH), "WATCH_RECURSIVE", "true" if cfg["recursive"] else "false")
    set_key(str(ENV_PATH), "WATCH_EXTENSIONS", ",".join(cfg["extensions"]))
    set_key(str(ENV_PATH), "SSH_KEY_PATH", str(cfg["key_path"]))
    logging.info(f"Konfiguration gespeichert: {ENV_PATH}")


def ensure_host_known(cfg: dict):
    """Prüft ob der Host in known_hosts eingetragen ist. Falls nicht, einmalig per Passwort verbinden und Host-Key speichern."""
    known_hosts_path = KEY_DIR / "known_hosts"
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    if known_hosts_path.exists():
        client.load_host_keys(str(known_hosts_path))

    host_keys = client.get_host_keys()
    if cfg["host"] in host_keys:
        return

    print(f"\nHost {cfg['host']} nicht in known_hosts. Einmalige Verifizierung erforderlich.")
    password = getpass.getpass(f"Passwort fuer {cfg['user']}@{cfg['host']}: ")

    verifier = paramiko.SSHClient()
    verifier.load_system_host_keys()
    verifier.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        verifier.connect(
            hostname=cfg["host"],
            port=cfg["port"],
            username=cfg["user"],
            password=password,
            timeout=15,
            look_for_keys=False,
            allow_agent=False,
        )
        verifier.save_host_keys(str(known_hosts_path))
        print(f"Host-Key gespeichert: {known_hosts_path}")
    except paramiko.AuthenticationException:
        print("Authentifizierung fehlgeschlagen. Falsches Passwort?")
        sys.exit(1)
    except Exception as e:
        print(f"Verbindung fehlgeschlagen: {e}")
        sys.exit(1)
    finally:
        verifier.close()


def setup_ssh_key(cfg: dict):
    """Generiert ein RSA-Schlüsselpaar, überträgt den Public Key per Passwort-Auth
    auf den Server und speichert NUR den Private Key lokal."""

    KEY_DIR.mkdir(mode=0o700, exist_ok=True)

    print("\nErste Verbindung: SSH-Key wird erstellt und auf den Server uebertragen.")
    print("Bitte Passwort fuer die initiale Uebertragung eingeben.")
    password = getpass.getpass(f"Passwort fuer {cfg['user']}@{cfg['host']}: ")

    # Schlüsselpaar generieren (nur im RAM)
    print("Erstelle RSA-4096-Schluesselpaar...")
    key = paramiko.RSAKey.generate(4096)

    # Public Key als String (bleibt im RAM, wird NICHT auf Disk geschrieben)
    pub_key_str = f"ssh-rsa {key.get_base64()} securesync@{cfg['host']}"

    # Mit Passwort verbinden und Public Key in authorized_keys eintragen
    known_hosts_path = KEY_DIR / "known_hosts"
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        print(f"Verbinde mit {cfg['user']}@{cfg['host']}:{cfg['port']} ...")
        client.connect(
            hostname=cfg["host"],
            port=cfg["port"],
            username=cfg["user"],
            password=password,
            timeout=15,
            look_for_keys=False,
            allow_agent=False,
        )
        # Host-Key in known_hosts speichern damit spätere Verbindungen ihn kennen
        client.save_host_keys(str(known_hosts_path))
        print(f"Host-Key gespeichert: {known_hosts_path}")

        command = (
            'mkdir -p ~/.ssh && '
            'chmod 700 ~/.ssh && '
            f'echo "{pub_key_str}" >> ~/.ssh/authorized_keys && '
            'chmod 600 ~/.ssh/authorized_keys'
        )
        stdin, stdout, stderr = client.exec_command(command)
        exit_status = stdout.channel.recv_exit_status()

        if exit_status != 0:
            err = stderr.read().decode().strip()
            print(f"Fehler beim Eintragen des Keys auf dem Server: {err}")
            sys.exit(1)

        print("Public Key erfolgreich auf Server eingetragen.")

    except paramiko.AuthenticationException:
        print("Authentifizierung fehlgeschlagen. Falsches Passwort?")
        sys.exit(1)
    except Exception as e:
        print(f"Verbindung fehlgeschlagen: {e}")
        sys.exit(1)
    finally:
        client.close()

    # Nur Private Key lokal speichern – Public Key wird nicht auf Disk geschrieben
    key.write_private_key_file(str(PRIVATE_KEY_PATH))
    os.chmod(PRIVATE_KEY_PATH, 0o600)
    cfg["key_path"] = PRIVATE_KEY_PATH
    print(f"Privater Key gespeichert: {PRIVATE_KEY_PATH}")
    print("Oeffentlicher Key wurde NICHT lokal gespeichert.")


def run_setup() -> dict:
    print("=== SecureSync Einrichtung ===\n")

    host = input("SSH Host/IP: ").strip()
    while not host:
        host = input("  (erforderlich) SSH Host/IP: ").strip()

    port_input = input("SSH Port [22]: ").strip()
    port = int(port_input) if port_input.isdigit() else 22

    user = input("SSH Benutzer: ").strip()
    while not user:
        user = input("  (erforderlich) SSH Benutzer: ").strip()

    default_remote = f"/home/{user}/uploads"
    remote_dir = input(f"Remote-Verzeichnis [{default_remote}]: ").strip() or default_remote

    watch_path = input("Lokales Verzeichnis zum Ueberwachen: ").strip()
    while not watch_path or not os.path.isdir(watch_path):
        if watch_path and not os.path.isdir(watch_path):
            print(f"  Verzeichnis nicht gefunden: {watch_path}")
        watch_path = input("Lokales Verzeichnis zum Ueberwachen: ").strip()

    recursive_input = input("Rekursiv ueberwachen? [j/N]: ").strip().lower()
    recursive = recursive_input in ("j", "y", "ja", "yes")

    extensions_input = input("Dateitypen filtern (z.B. .pdf,.txt) [leer = alle]: ").strip()
    extensions = [e.strip().lower() for e in extensions_input.split(",") if e.strip()]

    cfg = {
        "host": host,
        "port": port,
        "user": user,
        "remote_dir": remote_dir,
        "watch_path": watch_path,
        "recursive": recursive,
        "extensions": extensions,
        "key_path": PRIVATE_KEY_PATH,
    }

    # SSH-Key einrichten
    if not PRIVATE_KEY_PATH.exists():
        setup_ssh_key(cfg)
    else:
        print(f"\nVorhandener SSH-Key wird verwendet: {PRIVATE_KEY_PATH}")
        ensure_host_known(cfg)

    save_env(cfg)
    return cfg


def upload_file(cfg: dict, local_path: str):
    """Lädt eine Datei per SFTP auf den Remote-Server."""
    key_path = cfg.get("key_path", PRIVATE_KEY_PATH)
    if not Path(key_path).exists():
        logging.error(f"Private Key nicht gefunden: {key_path}")
        return

    file_name = Path(local_path).name
    remote_path = f"{cfg['remote_dir']}/{file_name}"

    known_hosts_path = KEY_DIR / "known_hosts"
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    if known_hosts_path.exists():
        client.load_host_keys(str(known_hosts_path))
    client.set_missing_host_key_policy(paramiko.RejectPolicy())
    try:
        client.connect(
            hostname=cfg["host"],
            port=cfg["port"],
            username=cfg["user"],
            key_filename=str(key_path),
            timeout=10,
            look_for_keys=False,
            allow_agent=False,
        )
        sftp = client.open_sftp()
        sftp.put(local_path, remote_path)
        sftp.close()
        logging.info(f"Hochgeladen: {file_name} -> {cfg['user']}@{cfg['host']}:{remote_path}")
    except Exception as e:
        logging.error(f"Upload fehlgeschlagen fuer {file_name}: {e}")
    finally:
        client.close()


class SyncHandler(FileSystemEventHandler):
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.extensions = cfg.get("extensions", [])

    def _allowed(self, path: str) -> bool:
        if not self.extensions:
            return True
        return Path(path).suffix.lower() in self.extensions

    def on_created(self, event):
        if not event.is_directory and self._allowed(event.src_path):
            logging.info(f"Neue Datei erkannt: {event.src_path}")
            upload_file(self.cfg, event.src_path)

    def on_modified(self, event):
        if not event.is_directory and self._allowed(event.src_path):
            logging.info(f"Datei geaendert: {event.src_path}")
            upload_file(self.cfg, event.src_path)


if __name__ == "__main__":
    cfg = load_env()

    if cfg is None:
        print("Keine vollstaendige Konfiguration in .env gefunden. Setup wird gestartet...")
        cfg = run_setup()
    elif not cfg["key_path"].exists():
        print(f"Konfiguration vorhanden, aber kein SSH-Key unter {cfg['key_path']}.")
        redo = input("Key neu erstellen und uebertragen? [J/n]: ").strip().lower()
        if redo not in ("n", "no", "nein"):
            setup_ssh_key(cfg)
            save_env(cfg)
        else:
            logging.error("Kein SSH-Key vorhanden. Abbruch.")
            sys.exit(1)
    else:
        ensure_host_known(cfg)

    watch_path = cfg["watch_path"]
    if not os.path.isdir(watch_path):
        logging.error(f"Ueberwachungsverzeichnis nicht gefunden: {watch_path}")
        sys.exit(1)

    ext_display = ", ".join(cfg["extensions"]) if cfg["extensions"] else "alle"
    logging.info(f"Ueberwache: {watch_path}  (rekursiv={cfg['recursive']})  (Typen: {ext_display})")
    logging.info(f"Hochladen nach: {cfg['user']}@{cfg['host']}:{cfg['remote_dir']}")

    handler = SyncHandler(cfg=cfg)
    observer = Observer()
    observer.schedule(handler, path=watch_path, recursive=cfg["recursive"])
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Beende Ueberwachung...")
        observer.stop()
    observer.join()
    logging.info("SecureSync gestoppt.")
