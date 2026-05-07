import paramiko

def run_command(client, command):
    stdin, stdout, stderr = client.exec_command(command)
    exit_code = stdout.channel.recv_exit_status()
    output = stdout.read().decode().strip()
    error = stderr.read().decode().strip()
    return exit_code, output, error

# Verbindungsparameter
print("=== SSH-Verbindung ===")
host     = input("Hostname/IP: ")
port     = int(input("Port (Standard: 22): ") or 22)
username = input("Benutzername (Admin): ")
password = input("Passwort (Admin): ")

# Neuer Benutzer
print("\n=== Neuer Benutzer ===")
new_user     = input("Neuer Benutzername: ")
new_password = input("Passwort für neuen Benutzer: ")

# SSH-Verbindung aufbauen
client = paramiko.SSHClient()
client.load_system_host_keys()
client.set_missing_host_key_policy(paramiko.RejectPolicy())

try:
    client.connect(hostname=host, port=port, username=username, password=password)
    print(f"\n✓ Verbunden mit {host}")

    # Benutzer erstellen
    print(f"  Erstelle Benutzer '{new_user}'...")
    code, out, err = run_command(client, f"sudo useradd -m -s /bin/bash {new_user}")
    if code != 0:
        raise Exception(f"useradd fehlgeschlagen: {err}")
    print(f"  ✓ Benutzer erstellt")

    # Passwort setzen
    print(f"  Setze Passwort...")
    code, out, err = run_command(client, f"echo '{new_user}:{new_password}' | sudo chpasswd")
    if code != 0:
        raise Exception(f"chpasswd fehlgeschlagen: {err}")
    print(f"  ✓ Passwort gesetzt")

    # Ergebnis prüfen
    code, out, err = run_command(client, f"id {new_user}")
    if code == 0:
        print(f"\n✓ Benutzer erfolgreich angelegt: {out}")
    else:
        print(f"  Warnung: Benutzer konnte nicht verifiziert werden: {err}")

except Exception as e:
    print(f"\n✗ Fehler: {e}")
except paramiko.AuthenticationException:
    print("✗ Authentifizierung fehlgeschlagen.")
except paramiko.SSHException as e:
    print(f"✗ SSH-Fehler: {e}")
finally:
    client.close()
    print("Verbindung geschlossen.")