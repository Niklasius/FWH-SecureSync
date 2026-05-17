import paramiko
import getpass
from pathlib import Path

host     = input("Hostname/IP: ")
port     = int(input("Port (Standard: 22): ") or 22)
username = input("Benutzername: ")
password = getpass.getpass("Passwort: ")

local_file  = Path(input("Lokale Datei (Pfad): ").strip())
remote_path = input("Remote Pfad (z.B. /home/[user]/datei.txt): ").strip()

client = paramiko.SSHClient()
client.load_system_host_keys()
client.set_missing_host_key_policy(paramiko.RejectPolicy())

try:
    client.connect(hostname=host, port=port, username=username, password=password)
    print(f"✓ Verbunden mit {host}")

    with client.open_sftp() as sftp:
        sftp.put(str(local_file), remote_path)
        print(f"✓ '{local_file.name}' → {remote_path}")

except FileNotFoundError:
    print(f"✗ Datei nicht gefunden: {local_file}")
except paramiko.AuthenticationException:
    print("✗ Authentifizierung fehlgeschlagen.")
except paramiko.SSHException as e:
    print(f"✗ SSH-Fehler: {e}")
finally:
    client.close()
    print("Verbindung geschlossen.")