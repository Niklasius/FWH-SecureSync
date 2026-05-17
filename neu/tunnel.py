import paramiko
import getpass
import socket
import threading

# ─────────────────────────────────────────
#  Verbindungsparameter
# ─────────────────────────────────────────
print("=== SSH Tunnel ===")
host     = input("SSH-Server (Hostname/IP): ")
port     = int(input("SSH-Port (Standard: 22): ") or 22)
username = input("Benutzername: ")
password = getpass.getpass("Passwort: ")

remote_host = input("Ziel-Host (z.B. datenbankserver): ")
remote_port = int(input("Ziel-Port (z.B. 5432 für PostgreSQL): "))
local_port  = int(input("Lokaler Port (z.B. 5432): ") or 5432)

# ─────────────────────────────────────────
#  Tunnel-Logik
# ─────────────────────────────────────────

def handle_connection(local_socket, transport, remote_host, remote_port):
    """Verbindet einen lokalen Socket mit dem Remote-Ziel durch den Tunnel."""
    try:
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

    # Daten in beide Richtungen weiterleiten
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

    threading.Thread(target=forward, args=(local_socket, tunnel), daemon=True).start()
    threading.Thread(target=forward, args=(tunnel, local_socket), daemon=True).start()


# ─────────────────────────────────────────
#  SSH-Verbindung + Tunnel starten
# ─────────────────────────────────────────

client = paramiko.SSHClient()
client.load_system_host_keys()
client.set_missing_host_key_policy(paramiko.RejectPolicy())

try:
    client.connect(hostname=host, port=port, username=username, password=password)
    print(f"\n✓ Verbunden mit {host}:{port}")

    transport = client.get_transport()

    # Lokalen Server starten der auf Verbindungen wartet
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("localhost", local_port))
    server.listen(5)

    print(f"✓ Tunnel aktiv: localhost:{local_port} → {remote_host}:{remote_port}")
    print("  Verbinde jetzt dein Tool auf localhost:" + str(local_port))
    print("  STRG+C zum Beenden\n")

    while True:
        local_socket, addr = server.accept()
        print(f"  Neue Verbindung von {addr}")
        threading.Thread(
            target=handle_connection,
            args=(local_socket, transport, remote_host, remote_port),
            daemon=True
        ).start()

except KeyboardInterrupt:
    print("\n\nTunnel beendet.")
except paramiko.AuthenticationException:
    print("✗ Authentifizierung fehlgeschlagen.")
except paramiko.SSHException as e:
    print(f"✗ SSH-Fehler: {e}")
finally:
    client.close()
    print("Verbindung geschlossen.")