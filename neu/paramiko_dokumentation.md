# Paramiko – Dokumentation

## Was ist Paramiko?

Paramiko ist eine Python-Bibliothek, die das **SSHv2-Protokoll** vollständig in reinem Python implementiert. Sie ermöglicht es, SSH-Verbindungen aufzubauen, Befehle auf Remote-Servern auszuführen, Dateien via SFTP zu übertragen und SSH-Tunnel zu erstellen – ohne externe Tools wie `ssh` oder `scp`.

```bash
pip install paramiko
```

---

## Verbindungsaufbau – Grundstruktur

Jede Paramiko-Verbindung folgt demselben Grundprinzip:

1. `SSHClient`-Objekt erstellen
2. Host-Key-Policy festlegen
3. Verbindung aufbauen (`connect()`)
4. Aktionen ausführen
5. Verbindung schließen (`close()`)

Der `connect()`-Aufruf nimmt mindestens `hostname`, `port` und `username` entgegen – die **Authentifizierung** wird darüber hinaus konfiguriert.

---

## Host-Key-Verifizierung

Bevor die eigentliche Authentifizierung stattfindet, prüft Paramiko den **Host-Key des Servers** (vergleichbar mit dem Fingerprint beim ersten `ssh`-Login).

### Verfügbare Policies

**`RejectPolicy`** *(empfohlen)*
Unbekannte Host-Keys werden abgelehnt. Der Server muss vorher in `~/.ssh/known_hosts` eingetragen sein. Schützt vor Man-in-the-Middle-Angriffen.

```python
client.load_system_host_keys()
client.set_missing_host_key_policy(paramiko.RejectPolicy())
```

**`AutoAddPolicy`**
Unbekannte Host-Keys werden automatisch akzeptiert und gespeichert. Praktisch für Testumgebungen, aber unsicher in Produktion – der Server wird nie verifiziert.

```python
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
```

**`WarningPolicy`**
Akzeptiert unbekannte Keys, gibt aber eine Warnung aus. Kompromiss zwischen den beiden obigen Optionen.

```python
client.set_missing_host_key_policy(paramiko.WarningPolicy())
```

---

## Authentifizierungsmethoden

### 1. Passwort-Authentifizierung

Die einfachste Methode: Benutzername und Passwort werden direkt an `connect()` übergeben.

```python
client.connect(
    hostname="192.168.1.10",
    port=22,
    username="niklas",
    password="meinPasswort"
)
```

**Wann sinnvoll:**
- Schnelle Skripte in kontrollierten Umgebungen
- Wenn kein SSH-Key eingerichtet ist

**Nachteile:**
- Passwort im Skript oder Speicher vorhanden
- Weniger sicher als Key-Authentifizierung
- Automatisierung schwieriger (Passwort muss irgendwo herkommen)

**Passwort sicher abfragen** statt hartkodieren:

```python
import getpass
password = getpass.getpass("Passwort: ")
```

`getpass` liest die Eingabe ohne Echo im Terminal – das Passwort wird nicht angezeigt. Alle Skripte im Projekt verwenden genau diese Methode.

---

### 2. SSH-Key-Authentifizierung

Statt eines Passworts wird ein **kryptografisches Schlüsselpaar** verwendet:
- **Private Key** – bleibt auf dem Client (niemals weitergeben)
- **Public Key** – wird auf dem Server in `~/.ssh/authorized_keys` eingetragen

Paramiko unterstützt alle gängigen Key-Typen: **RSA**, **Ed25519**, **ECDSA**, **DSA**.

#### Schlüsselpaar generieren

Mit Python und Paramiko lässt sich direkt ein Key-Paar erstellen:

```python
import paramiko

# Ed25519-Key erzeugen (modern, empfohlen)
key = paramiko.Ed25519Key.generate()

# Private Key speichern
key.write_private_key_file("/home/user/.ssh/id_ed25519")

# Public Key ausgeben (für authorized_keys auf dem Server)
print(key.get_base64())
```

Alternativ via Terminal:
```bash
ssh-keygen -t ed25519 -C "kommentar"
```

#### Verbinden mit Key-Datei

```python
client.connect(
    hostname="192.168.1.10",
    port=22,
    username="niklas",
    key_filename="/home/niklas/.ssh/id_ed25519"
)
```

Paramiko erkennt den Key-Typ automatisch anhand der Datei.

#### Verbinden mit Key-Objekt (im Speicher)

```python
private_key = paramiko.Ed25519Key.from_private_key_file("/home/niklas/.ssh/id_ed25519")

client.connect(
    hostname="192.168.1.10",
    port=22,
    username="niklas",
    pkey=private_key
)
```

#### Key mit Passphrase

Ein Private Key kann zusätzlich mit einer Passphrase gesichert sein:

```python
private_key = paramiko.RSAKey.from_private_key_file(
    "/home/niklas/.ssh/id_rsa",
    password="key-passphrase"
)
```

#### Public Key auf den Server übertragen

Nach dem Generieren muss der Public Key auf den Server. Das kann manuell oder automatisch per SFTP geschehen:

```python
# Verbindung zunächst mit Passwort aufbauen
client.connect(hostname=host, username=username, password=password)

# Public Key an authorized_keys anhängen
pub_key_line = f"ssh-ed25519 {key.get_base64()}\n"
with client.open_sftp() as sftp:
    with sftp.open("/home/niklas/.ssh/authorized_keys", "a") as f:
        f.write(pub_key_line)
```

---

### Passwort vs. SSH-Key – Vergleich

| Kriterium | Passwort | SSH-Key |
|---|---|---|
| Sicherheit | Mittel | Hoch |
| Automatisierung | Aufwändig | Einfach |
| Einrichtung | Keine | Key generieren + deployen |
| Brute-Force-Schutz | Nein | Ja (mathematisch sicher) |
| Passphrase möglich | — | Ja (zusätzliche Sicherheitsschicht) |
| Empfohlen für Produktion | Nein | Ja |

---

## Verbindungsparameter im Überblick

`connect()` bietet weitere Parameter zur Feineinstellung:

| Parameter | Typ | Beschreibung |
|---|---|---|
| `hostname` | `str` | IP-Adresse oder Hostname des Servers |
| `port` | `int` | SSH-Port (Standard: `22`) |
| `username` | `str` | Benutzername auf dem Remote-System |
| `password` | `str` | Passwort (Methode 1) |
| `pkey` | `PKey` | Key-Objekt direkt übergeben (Methode 2) |
| `key_filename` | `str` | Pfad zur Key-Datei (Methode 2) |
| `timeout` | `float` | Verbindungs-Timeout in Sekunden |
| `allow_agent` | `bool` | SSH-Agent des Systems nutzen (Standard: `True`) |
| `look_for_keys` | `bool` | Automatisch in `~/.ssh/` nach Keys suchen (Standard: `True`) |
| `compress` | `bool` | Datenkomprimierung aktivieren |
| `auth_timeout` | `float` | Timeout speziell für die Authentifizierung |

**Beispiel mit mehreren Parametern:**

```python
client.connect(
    hostname="192.168.1.10",
    port=22,
    username="niklas",
    key_filename="/home/niklas/.ssh/id_ed25519",
    timeout=10,
    look_for_keys=False,   # nur den angegebenen Key verwenden
    allow_agent=False       # SSH-Agent deaktivieren
)
```

---

## Aktionsmöglichkeiten nach der Verbindung

Nach dem erfolgreichen `connect()` stehen verschiedene Aktionen zur Verfügung:

### Befehle ausführen – `exec_command()`

Für einzelne, nicht-interaktive Befehle. Gibt drei Streams zurück (`stdin`, `stdout`, `stderr`). Der Exit-Code ist über `stdout.channel.recv_exit_status()` abrufbar. Im Projekt genutzt in `ssh_echo.py` und `neuer_Benutzer.py`.

### Interaktive Shell – `invoke_shell()`

Öffnet ein echtes PTY (Pseudo-Terminal). Notwendig für Befehle die eine Terminal-Umgebung erwarten, wie `sudo`, interaktive Programme oder mehrzeilige Eingaben. Kommunikation läuft über `shell.send()` und `shell.recv()`. Im Projekt genutzt in `PTY.py`.

### Dateitransfer – `open_sftp()`

Öffnet eine SFTP-Session für Dateioperationen: Upload (`put`), Download (`get`), Verzeichnisse auflisten, erstellen und löschen. Im Projekt genutzt in `upload.py`.

### SSH-Tunnel – `get_transport()`

Gibt den Transport-Layer der Verbindung zurück. Darüber können mit `open_channel("direct-tcpip", ...)` TCP-Verbindungen durch den SSH-Tunnel geleitet werden. Jede Verbindung wird in einem eigenen Thread weitergeleitet. Im Projekt genutzt in `tunnel.py`.

---

## Fehlerbehandlung

Die drei wichtigsten Exceptions:

| Exception | Ursache |
|---|---|
| `paramiko.AuthenticationException` | Falsches Passwort, Key nicht akzeptiert |
| `paramiko.SSHException` | SSH-Protokollfehler, Verbindungsabbruch |
| `Exception` | Netzwerkfehler, Host nicht erreichbar, etc. |

`client.close()` gehört immer in den `finally`-Block, damit die Verbindung auch bei Fehlern sauber getrennt wird.
