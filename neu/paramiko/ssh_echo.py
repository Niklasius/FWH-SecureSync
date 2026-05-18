# ─────────────────────────────────────────
#  Paramiko – SSH Echo
#  Baut eine SSH-Verbindung per Passwort auf
#  und führt einen einfachen Echo-Befehl aus.
# ─────────────────────────────────────────

import paramiko

# ─────────────────────────────────────────
#  Verbindungsparameter
# ─────────────────────────────────────────
print("=== Paramiko – SSH Echo ===")
host     = input("Hostname/IP: ")
port     = int(input("Port (Standard: 22): ") or 22)
username = input("Benutzername: ")
password = input("Passwort: ")

# ─────────────────────────────────────────
#  SSH-Client aufbauen
# ─────────────────────────────────────────

# Client-Objekt erstellen und System-Host-Keys laden (aus ~/.ssh/known_hosts)
client = paramiko.SSHClient()
client.load_system_host_keys()

# RejectPolicy: unbekannte Server-Keys werden abgelehnt → schützt vor MITM
client.set_missing_host_key_policy(paramiko.RejectPolicy())

# ─────────────────────────────────────────
#  Verbindung + Befehl
# ─────────────────────────────────────────

try:
    client.connect(hostname=host, port=port, username=username, password=password)
    print(f"✓ Verbunden mit {host}")

    # exec_command() führt einen einzelnen Befehl aus (kein PTY, nicht-interaktiv)
    # Rückgabe: drei Stream-Objekte für stdin, stdout und stderr
    command = 'echo "Hallo vom Server!"'
    stdin, stdout, stderr = client.exec_command(command)

    # Ausgabe lesen, dekodieren und Whitespace entfernen
    output = stdout.read().decode().strip()
    error  = stderr.read().decode().strip()

    if output:
        print(f"Ausgabe: {output}")
    if error:
        print(f"Fehler:  {error}")

# ─────────────────────────────────────────
#  Fehlerbehandlung
# ─────────────────────────────────────────

except paramiko.AuthenticationException:
    print("✗ Authentifizierung fehlgeschlagen.")
except paramiko.SSHException as e:
    print(f"✗ SSH-Fehler: {e}")
finally:
    # Verbindung schließen
    client.close()
    print("Verbindung geschlossen.")
