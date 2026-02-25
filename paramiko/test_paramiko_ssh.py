import paramiko
import sys       # Ermöglicht sauberes Beenden des Programms bei Fehlern

#  Authentifizierung für den Debian-Server
SSH_HOST = "192.168.2.124"  # Die IP-Adresse der Debian-VM
SSH_USER = "securesync" # Der User, den wir bei der Installation erstellt haben
SSH_PASS = ""    # Das zugehörige Passwort

def connect_to_server():
    # Diese Funktion baut eine verschlüsselte Verbindung zum Server auf,
    # führt einen Testbefehl aus und schließt die Verbindung wieder.
    
    # 1. SSH-Client Objekt erstellen:
    # quasi das 'Telefon', mit dem wir den Server anrufen.
    client = paramiko.SSHClient()
    
    # 2. Sicherheits-Policy setzen:
    # Da unser Client den Debian-Server noch nicht "kennt", würde SSH normalerweise fragen:
    # 'Vertraust du diesem Server ?' (Key-Verifikation).
    # AutoAddPolicy() sagt: 'Ja, füge den Server-Schlüssel automatisch hinzu.'
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        print(f"--- Starte Verbindungsaufbau zu {SSH_HOST} ---")
        
        # 3.(Login):
        # Wir übergeben IP, User und das Passwort. 
        # timeout=10 verhindert, dass das Skript ewig hängt, wenn der Server offline ist.
        client.connect(
            hostname=SSH_HOST, 
            username=SSH_USER, 
            password=SSH_PASS, 
            timeout=10
        )
        
        print("✅ Authentifizierung erfolgreich: Die Tür ist offen.")

        # 4. Einen Befehl auf dem fernen System ausführen:
        # exec_command sendet den String direkt an die Debian-Bash.
        # Wir erhalten drei 'Kanäle': 
        # stdin (Eingabe), stdout (Standard-Ausgabe), stderr (Fehlermeldungen).
        stdin, stdout, stderr = client.exec_command('uptime')
        
        # Die Antwort vom Server muss von 'Bytes' in 'Text' (UTF-8) umgewandelt werden.
        output = stdout.read().decode('utf-8').strip()
        print(f"🐧 Nachricht vom Debian-Server: {output}")

        return True

    except paramiko.AuthenticationException:
        # Tritt auf, wenn User oder Passwort nicht stimmen.
        print("❌ Login-Fehler: Überprüfe User und Passwort in der Debian-VM.")
    except paramiko.SSHException as e:
        # Tritt auf, wenn es Probleme mit dem SSH-Protokoll gibt.
        print(f"❌ SSH-Protokollfehler: {e}")
    except Exception as e:
        # Fängt alle anderen Fehler ab (z.B. falsche IP oder "Server ist aus").
        print(f"❌ Netzwerkfehler: {e}")
    finally:
        # 5. Die Verbindung sauber trennen:
        # Das ist extrem wichtig, damit auf dem Server keine 'toten' Sitzungen 
        # offen bleiben, die irgendwann den Speicher füllen.
        client.close()
        print("--- Verbindung geschlossen und Ressourcen freigegeben ---")
        return False

if __name__ == "__main__":
    connect_to_server()