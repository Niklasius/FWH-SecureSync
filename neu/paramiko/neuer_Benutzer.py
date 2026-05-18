# ─────────────────────────────────────────
#  Paramiko – Neuen Benutzer anlegen
#  Verbindet per SSH und legt über
#  exec_command() einen neuen Linux-User an.
# ─────────────────────────────────────────

import paramiko

# ─────────────────────────────────────────
#  Hilfsfunktion
# ─────────────────────────────────────────

def run_command(client, command):
    """Führt einen Befehl aus und gibt Exit-Code, Output und Fehler zurück."""
    stdin, stdout, stderr = client.exec_command(command)
    exit_code = stdout.channel.recv_exit_status()   # blockiert bis Befehl abgeschlossen
    output    = stdout.read().decode().strip()
    error     = stderr.read().decode().strip()
    return exit_code, output, error

# ─────────────────────────────────────────
#  Verbindungsparameter
# ─────────────────────────────────────────
print("=== Paramiko – Neuen Benutzer anlegen ===")
host     = input("Hostname/IP: ")
port     = int(input("Port (Standard: 22): ") or 22)
username = input("Benutzername (Admin): ")
password = input("Passwort (Admin): ")

# ─────────────────────────────────────────
#  Neuer Benutzer
# ─────────────────────────────────────────
print("\n=== Neuer Benutzer ===")
new_user     = input("Neuer Benutzername: ")
new_password = input("Passwort für neuen Benutzer: ")

# ─────────────────────────────────────────
#  SSH-Client aufbauen
# ─────────────────────────────────────────

# Client-Objekt erstellen und System-Host-Keys laden (aus ~/.ssh/known_hosts)
client = paramiko.SSHClient()
client.load_system_host_keys()

# RejectPolicy: unbekannte Server-Keys werden abgelehnt → schützt vor MITM
client.set_missing_host_key_policy(paramiko.RejectPolicy())

# ─────────────────────────────────────────
#  Verbindung + Benutzer anlegen
# ─────────────────────────────────────────

try:
    client.connect(hostname=host, port=port, username=username, password=password)
    print(f"\n✓ Verbunden mit {host}")

    # useradd mit -m (Home-Verzeichnis erstellen) und -s (Standard-Shell setzen)
    print(f"  Erstelle Benutzer '{new_user}'...")
    code, out, err = run_command(client, f"sudo useradd -m -s /bin/bash {new_user}")
    if code != 0:
        raise Exception(f"useradd fehlgeschlagen: {err}")
    print(f"  ✓ Benutzer erstellt")

    # chpasswd liest Paare im Format "user:passwort" von stdin und setzt das Passwort
    print(f"  Setze Passwort...")
    code, out, err = run_command(client, f"echo '{new_user}:{new_password}' | sudo chpasswd")
    if code != 0:
        raise Exception(f"chpasswd fehlgeschlagen: {err}")
    print(f"  ✓ Passwort gesetzt")

    # `id` gibt UID, primäre GID und alle Gruppen des Benutzers aus → Verifikation
    code, out, err = run_command(client, f"id {new_user}")
    if code == 0:
        print(f"\n✓ Benutzer erfolgreich angelegt: {out}")
    else:
        print(f"  Warnung: Benutzer konnte nicht verifiziert werden: {err}")

# ─────────────────────────────────────────
#  Fehlerbehandlung
# ─────────────────────────────────────────

except Exception as e:
    print(f"\n✗ Fehler: {e}")
except paramiko.AuthenticationException:
    print("✗ Authentifizierung fehlgeschlagen.")
except paramiko.SSHException as e:
    print(f"✗ SSH-Fehler: {e}")
finally:
    # Verbindung schließen
    client.close()
    print("Verbindung geschlossen.")
