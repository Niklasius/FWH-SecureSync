# ─────────────────────────────────────────
#  Paramiko – PTY / Interaktive Shell
#  Öffnet ein echtes Pseudo-Terminal und
#  führt Befehle inkl. sudo interaktiv aus.
# ─────────────────────────────────────────

import paramiko
import getpass
import time

# ─────────────────────────────────────────
#  Verbindungsparameter
# ─────────────────────────────────────────
print("=== Paramiko – PTY / Interaktive Shell ===")
host      = input("Hostname/IP: ")
port      = int(input("Port (Standard: 22): ") or 22)
username  = input("Benutzername: ")
password  = getpass.getpass("Passwort: ")

# Sudo-Passwort separat abfragen – oft identisch, kann aber abweichen
sudo_pass = getpass.getpass("Sudo-Passwort (leer = gleich wie oben): ") or password

# ─────────────────────────────────────────
#  Hilfsfunktion
# ─────────────────────────────────────────

def send_command(shell, command: str, wait: float = 1.0) -> str:
    """Sendet einen Befehl an die Shell und liest die Ausgabe nach `wait` Sekunden."""
    shell.send(command + "\n")
    time.sleep(wait)         # kurz warten bis der Befehl Ausgabe produziert hat
    output = ""
    while shell.recv_ready():
        output += shell.recv(4096).decode()
    return output.strip()

# ─────────────────────────────────────────
#  SSH-Client aufbauen
# ─────────────────────────────────────────

# Client-Objekt erstellen und System-Host-Keys laden (aus ~/.ssh/known_hosts)
client = paramiko.SSHClient()
client.load_system_host_keys()

# RejectPolicy: unbekannte Server-Keys werden abgelehnt → schützt vor MITM
client.set_missing_host_key_policy(paramiko.RejectPolicy())

# ─────────────────────────────────────────
#  Verbindung + PTY
# ─────────────────────────────────────────

try:
    client.connect(hostname=host, port=port, username=username, password=password)
    print(f"\n✓ Verbunden mit {host}")

    # invoke_shell() öffnet ein echtes PTY – nötig für sudo, vim, less, etc.
    # term="xterm" simuliert ein Standard-Terminal, width/height definieren die Fenstergröße
    shell = client.invoke_shell(term="xterm", width=220, height=50)
    time.sleep(0.5)
    shell.recv(4096)    # initiale Willkommensnachricht des Servers wegwerfen

    print("✓ PTY Shell geöffnet\n")

    # ── Normaler Befehl ──
    print("─── whoami ───")
    out = send_command(shell, "whoami")
    print(out)

    # ── sudo mit Passwort ──
    print("\n─── sudo apt update (mit Passwort) ───")
    shell.send("sudo apt update\n")
    time.sleep(1.5)

    output = shell.recv(4096).decode()
    print(output)

    # sudo fragt ggf. nach dem Passwort – Antwort automatisch einspeisen
    if "password" in output.lower() or "passwort" in output.lower():
        print("  → Sudo-Passwort wird gesendet...")
        shell.send(sudo_pass + "\n")
        time.sleep(2.0)
        while shell.recv_ready():
            print(shell.recv(4096).decode(), end="")

    # ── Live-Output (tail) ──
    print("\n─── tail -n 5 /var/log/syslog ───")
    out = send_command(shell, "tail -n 5 /var/log/syslog", wait=1.5)
    print(out)

    # ── Interaktiver Modus ──
    # Eigene Befehle manuell eingeben; "exit" oder "quit" beendet die Schleife
    print("\n─── Interaktiver Modus (exit zum Beenden) ───")
    while True:
        cmd = input("shell> ").strip()
        if cmd.lower() in ("exit", "quit", ""):
            break
        out = send_command(shell, cmd, wait=1.0)
        print(out)

# ─────────────────────────────────────────
#  Fehlerbehandlung
# ─────────────────────────────────────────

except paramiko.AuthenticationException:
    print("✗ Authentifizierung fehlgeschlagen.")
except paramiko.SSHException as e:
    print(f"✗ SSH-Fehler: {e}")
except Exception as e:
    print(f"✗ Fehler: {e}")
finally:
    # Verbindung schließen
    client.close()
    print("\nVerbindung geschlossen.")
