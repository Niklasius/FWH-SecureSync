import paramiko
import getpass
import time

# ─────────────────────────────────────────
#  Verbindungsparameter
# ─────────────────────────────────────────
print("=== PTY / Interaktive Shell ===")
host      = input("Hostname/IP: ")
port      = int(input("Port (Standard: 22): ") or 22)
username  = input("Benutzername: ")
password  = getpass.getpass("Passwort: ")
sudo_pass = getpass.getpass("Sudo-Passwort (leer = gleich wie oben): ") or password

# ─────────────────────────────────────────
#  Hilfsfunktion
# ─────────────────────────────────────────

def send_command(shell, command: str, wait: float = 1.0) -> str:
    """Sendet einen Befehl und liest die Ausgabe."""
    shell.send(command + "\n")
    time.sleep(wait)
    output = ""
    while shell.recv_ready():
        output += shell.recv(4096).decode()
    return output.strip()


# ─────────────────────────────────────────
#  Verbindung + PTY
# ─────────────────────────────────────────

client = paramiko.SSHClient()
client.load_system_host_keys()
client.set_missing_host_key_policy(paramiko.RejectPolicy())

try:
    client.connect(hostname=host, port=port, username=username, password=password)
    print(f"\n✓ Verbunden mit {host}")

    # Interaktive Shell mit PTY öffnen
    shell = client.invoke_shell(term="xterm", width=220, height=50)
    time.sleep(0.5)
    shell.recv(4096)  # Willkommensnachricht wegwerfen

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

    # Passwort senden falls sudo danach fragt
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

    # ── Interaktiver Modus ───────────────
    print("\n─── Interaktiver Modus (exit zum Beenden) ───")
    while True:
        cmd = input("shell> ").strip()
        if cmd.lower() in ("exit", "quit", ""):
            break
        out = send_command(shell, cmd, wait=1.0)
        print(out)

except paramiko.AuthenticationException:
    print("✗ Authentifizierung fehlgeschlagen.")
except paramiko.SSHException as e:
    print(f"✗ SSH-Fehler: {e}")
except Exception as e:
    print(f"✗ Fehler: {e}")
finally:
    client.close()
    print("\nVerbindung geschlossen.")