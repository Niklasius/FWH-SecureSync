import paramiko

HOST = "192.168.1.124"
PORT = 22
USER = "sysadmin"
PASSWORD = "Pa$$w0rd"

client = paramiko.SSHClient()
client.load_system_host_keys()
client.set_missing_host_key_policy(paramiko.RejectPolicy())

try:
    client.connect(HOST, port=PORT, username=USER, password=PASSWORD)
    print("Erfolgreich verbunden!")

    stdin, stdout, stderr = client.exec_command("uname -a")
    print(stdout.read().decode())

except paramiko.AuthenticationException:
    print("Fehler: Falsches Passwort oder Benutzername")
except paramiko.NoValidConnectionsError:
    print("Fehler: Server nicht erreichbar")
finally:
    client.close()