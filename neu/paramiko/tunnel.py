# ─────────────────────────────────────────
#  Paramiko – SSH Tunnel
#  Erstellt einen lokalen Port-Forward durch
#  einen SSH-Server (Local Port Forwarding).
# ─────────────────────────────────────────

import paramiko
import getpass
import socket
import threading

# ─────────────────────────────────────────
#  Verbindungsparameter
# ─────────────────────────────────────────
print("=== Paramiko – SSH Tunnel ===")
host     = input("SSH-Server (Hostname/IP): ")
port     = int(input("SSH-Port (Standard: 22): ") or 22)
username = input("Benutzername: ")
password = getpass.getpass("Passwort: ")

# Ziel hinter dem SSH-Server (z.B. ein Datenbankserver im internen Netz)
remote_host = input("Ziel-Host (z.B. datenbankserver): ")
remote_port = int(input("Ziel-Port (z.B. 5432 für PostgreSQL): "))

# Lokaler Port, auf dem der Tunnel erreichbar sein soll
local_port  = int(input("Lokaler Port (z.B. 5432): ") or 5432)

# ─────────────────────────────────────────
#  Tunnel-Logik
# ─────────────────────────────────────────

def handle_connection(local_socket, transport, remote_host, remote_port):
    """Verbindet einen lokalen Socket mit dem Remote-Ziel durch den SSH-Tunnel."""
    try:
        # direct-tcpip öffnet einen Kanal vom SSH-Server zum Ziel-Host
        tunnel = transport.open_channel(
            "direct-tcpip",
            (remote_host, remote_port),
            local_socket.getpeername()
        )
    except Exception as e:
        print(f"✗ Tunnel-Kanal konnte nicht geöffnet werden: {e}")
        local_socket.close()
        return

    print(f"✓ Tunnel geöffnet: localhost:{local_port} → {remote_host}:{remote_port}")

    # Datenpakete in beide Richtungen weiterleiten (bidirektionales Relay)
    def forward(src, dst):
        try:
            while True:
                data = src.recv(1024)
                if not data:
                    break
                dst.send(data)
        except Exception:
            pass
        finally:
            src.close()
            dst.close()

    # Jede Richtung läuft in einem eigenen Daemon-Thread
    threading.Thread(target=forward, args=(local_socket, tunnel), daemon=True).start()
    threading.Thread(target=forward, args=(tunnel, local_socket), daemon=True).start()

# ─────────────────────────────────────────
#  SSH-Client aufbauen
# ─────────────────────────────────────────

# Client-Objekt erstellen und System-Host-Keys laden (aus ~/.ssh/known_hosts)
client = paramiko.SSHClient()
client.load_system_host_keys()

# RejectPolicy: unbekannte Server-Keys werden abgelehnt → schützt vor MITM
client.set_missing_host_key_policy(paramiko.RejectPolicy())

# ─────────────────────────────────────────
#  Verbindung + Tunnel starten
# ─────────────────────────────────────────

try:
    client.connect(hostname=host, port=port, username=username, password=password)
    print(f"\n✓ Verbunden mit {host}:{port}")

    # Transport-Layer holen – darüber werden die Tunnel-Kanäle geöffnet
    transport = client.get_transport()

    # Lokalen TCP-Server starten, der auf eingehende Verbindungen wartet
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Port sofort wiederverwendbar
    server.bind(("localhost", local_port))
    server.listen(5)

    print(f"✓ Tunnel aktiv: localhost:{local_port} → {remote_host}:{remote_port}")
    print("  Verbinde jetzt dein Tool auf localhost:" + str(local_port))
    print("  STRG+C zum Beenden\n")

    # Hauptschleife: jede neue Verbindung bekommt einen eigenen Handler-Thread
    while True:
        local_socket, addr = server.accept()
        print(f"  Neue Verbindung von {addr}")
        threading.Thread(
            target=handle_connection,
            args=(local_socket, transport, remote_host, remote_port),
            daemon=True
        ).start()

# ─────────────────────────────────────────
#  Fehlerbehandlung
# ─────────────────────────────────────────

except KeyboardInterrupt:
    print("\n\nTunnel beendet.")
except paramiko.AuthenticationException:
    print("✗ Authentifizierung fehlgeschlagen.")
except paramiko.SSHException as e:
    print(f"✗ SSH-Fehler: {e}")
finally:
    # Verbindung schließen
    client.close()
    print("Verbindung geschlossen.")
