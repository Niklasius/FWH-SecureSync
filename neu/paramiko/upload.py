# ─────────────────────────────────────────
#  Paramiko – SFTP Upload
#  Überträgt eine lokale Datei per SFTP
#  auf einen entfernten Server.
# ─────────────────────────────────────────

import paramiko
import getpass
from pathlib import Path

# ─────────────────────────────────────────
#  Verbindungsparameter
# ─────────────────────────────────────────
print("=== Paramiko – SFTP Upload ===")
host     = input("Hostname/IP: ")
port     = int(input("Port (Standard: 22): ") or 22)
username = input("Benutzername: ")
password = getpass.getpass("Passwort: ")

# ─────────────────────────────────────────
#  Transfer-Parameter
# ─────────────────────────────────────────

# Path() normalisiert Tilde (~), Backslashes und relative Pfade automatisch
local_file  = Path(input("Lokale Datei (Pfad): ").strip())
remote_path = input("Remote Pfad (z.B. /home/[user]/datei.txt): ").strip()

# ─────────────────────────────────────────
#  SSH-Client aufbauen
# ─────────────────────────────────────────

# Client-Objekt erstellen und System-Host-Keys laden (aus ~/.ssh/known_hosts)
client = paramiko.SSHClient()
client.load_system_host_keys()

# RejectPolicy: unbekannte Server-Keys werden abgelehnt → schützt vor MITM
client.set_missing_host_key_policy(paramiko.RejectPolicy())

# ─────────────────────────────────────────
#  Verbindung + Upload
# ─────────────────────────────────────────

try:
    client.connect(hostname=host, port=port, username=username, password=password)
    print(f"✓ Verbunden mit {host}")

    # SFTP-Session als Context-Manager öffnen → wird automatisch geschlossen
    # sftp.put(lokaler_pfad, remote_pfad) überträgt die Datei byteweise
    with client.open_sftp() as sftp:
        sftp.put(str(local_file), remote_path)
        print(f"✓ '{local_file.name}' → {remote_path}")

# ─────────────────────────────────────────
#  Fehlerbehandlung
# ─────────────────────────────────────────

except FileNotFoundError:
    print(f"✗ Datei nicht gefunden: {local_file}")
except paramiko.AuthenticationException:
    print("✗ Authentifizierung fehlgeschlagen.")
except paramiko.SSHException as e:
    print(f"✗ SSH-Fehler: {e}")
finally:
    # Verbindung schließen
    client.close()
    print("Verbindung geschlossen.")
