import paramiko

# Verbindungsparameter
host = input("Hostname/IP: ")
port = int(input("Port (Standard: 22): ") or 22)
username = input("Benutzername: ")
password = input("Passwort: ")

# SSH-Client erstellen und verbinden
client = paramiko.SSHClient()
client.load_system_host_keys()
client.set_missing_host_key_policy(paramiko.RejectPolicy())

try:
    client.connect(hostname=host, port=port, username=username, password=password)
    print(f"✓ Verbunden mit {host}")

    # Echo-Befehl ausführen
    command = 'echo "Hallo vom Server!"'
    stdin, stdout, stderr = client.exec_command(command)

    output = stdout.read().decode().strip()
    error = stderr.read().decode().strip()

    # Echo-Befehl ausgeben
    if output:
        print(f"Ausgabe: {output}")
    if error:
        print(f"Fehler: {error}")

except paramiko.AuthenticationException:
    print("Fehler: Authentifizierung fehlgeschlagen.")
except paramiko.SSHException as e:
    print(f"SSH-Fehler: {e}")
finally:
    client.close()
    print("Verbindung geschlossen.")