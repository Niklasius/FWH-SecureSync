# SecureSync Client – Dokumentation

## Überblick

`securesync_client.py` ist ein automatischer Datei-Sync-Client, der ein lokales Verzeichnis überwacht und neu erstellte oder geänderte Dateien verschlüsselt per SFTP (SSH) auf einen Remote-Server hochlädt.

---

## Voraussetzungen

| Paket | Zweck |
|---|---|
| `paramiko` | SSH/SFTP-Verbindung |
| `watchdog` | Dateisystem-Überwachung |
| `python-dotenv` | Konfiguration über `.env`-Datei |

Installation:
```bash
pip install paramiko watchdog python-dotenv
```

---

## Konfiguration (`.env`)

Die Konfiguration wird in einer `.env`-Datei im selben Verzeichnis wie das Skript gespeichert.

| Variable | Beschreibung | Standard |
|---|---|---|
| `SSH_HOST` | Hostname oder IP des Servers | – (Pflichtfeld) |
| `SSH_PORT` | SSH-Port | `22` |
| `SSH_USER` | SSH-Benutzername | – (Pflichtfeld) |
| `SSH_KEY_PATH` | Pfad zum privaten SSH-Key | `~/.ssh/securesync_key` |
| `REMOTE_DIR` | Zielverzeichnis auf dem Server | `/home/<user>/uploads` |
| `WATCH_PATH` | Lokales Verzeichnis, das überwacht wird | – (Pflichtfeld) |
| `WATCH_RECURSIVE` | Unterverzeichnisse mit überwachen | `false` |
| `WATCH_EXTENSIONS` | Kommagetrennte Dateiendungen (z.B. `.pdf,.txt`) | leer = alle |

---

## Erststart & Setup

Beim ersten Start ohne gültige `.env` startet automatisch der interaktive Einrichtungsassistent:

```
=== SecureSync Einrichtung ===

SSH Host/IP: 192.168.1.100
SSH Port [22]:
SSH Benutzer: max
Remote-Verzeichnis [/home/max/uploads]:
Lokales Verzeichnis zum Ueberwachen: /home/max/dokumente
Rekursiv ueberwachen? [j/N]: j
Dateitypen filtern (z.B. .pdf,.txt) [leer = alle]: .pdf,.docx
```

### SSH-Key-Setup

Beim Erststart wird automatisch ein **RSA-4096-Schlüsselpaar** generiert:

- Der **private Key** wird lokal unter `~/.ssh/securesync_key` gespeichert (Rechte: `600`).
- Der **öffentliche Key** wird **nicht** lokal gespeichert, sondern direkt per Passwort-Authentifizierung in `~/.ssh/authorized_keys` auf dem Server eingetragen.
- Das eingegebene Passwort wird **nicht** gespeichert.

Nach dem Setup läuft die gesamte Authentifizierung nur noch über den SSH-Key – kein Passwort mehr nötig.

---

## Programmablauf

```
Start
  │
  ├─ .env vorhanden & vollständig?
  │     Nein → Interaktiver Setup-Assistent
  │     Ja   → SSH-Key vorhanden?
  │               Nein → Key neu erstellen? (Abfrage)
  │               Ja   → Host in known_hosts? Falls nicht: einmalige Verifikation
  │
  └─ Watchdog-Observer starten
        │
        └─ Ereignis: Datei erstellt / geändert
              │
              ├─ Dateiendung erlaubt?
              └─ SFTP-Upload auf Server
```

---

## Funktionsreferenz

### `load_env() → dict | None`
Lädt die `.env`-Datei und gibt die Konfiguration als Dictionary zurück. Gibt `None` zurück, wenn Pflichtfelder fehlen.

### `save_env(cfg: dict)`
Schreibt alle Konfigurationswerte in die `.env`-Datei.

### `ensure_host_known(cfg: dict)`
Prüft, ob der Server bereits in `~/.ssh/known_hosts` eingetragen ist. Falls nicht, wird einmalig eine Passwort-Verbindung aufgebaut und der Host-Key gespeichert.

### `setup_ssh_key(cfg: dict)`
Generiert ein RSA-4096-Schlüsselpaar im RAM, überträgt den Public Key per Passwort-Auth auf den Server und speichert nur den Private Key lokal.

### `run_setup() → dict`
Interaktiver Einrichtungsassistent. Fragt alle nötigen Parameter ab, richtet den SSH-Key ein und speichert die Konfiguration.

### `upload_file(cfg: dict, local_path: str)`
Lädt eine einzelne Datei per SFTP auf den Server. Erstellt das Remote-Verzeichnis automatisch, falls es noch nicht existiert. Verbindung wird nach jedem Upload geschlossen.

### `SyncHandler` (Klasse)
Watchdog-Event-Handler. Reagiert auf `on_created`- und `on_modified`-Ereignisse und ruft `upload_file` auf, sofern die Dateiendung erlaubt ist.

---

## Logging

Alle Ereignisse werden gleichzeitig in die Konsole und in `transfer.log` (im Skript-Verzeichnis) geschrieben.

Format: `YYYY-MM-DD HH:MM:SS - LEVEL - Nachricht`

Beispiel:
```
2026-03-20 14:32:01 - INFO - Neue Datei erkannt: /home/max/dokumente/bericht.pdf
2026-03-20 14:32:02 - INFO - Hochgeladen: bericht.pdf -> max@192.168.1.100:/home/max/uploads/bericht.pdf
```

---

## Sicherheitshinweise

- Die SSH-Verbindung verwendet ausschließlich Key-Authentifizierung (kein Passwort im Dauerbetrieb).
- Unbekannte Host-Keys werden **abgelehnt** (`RejectPolicy`) – kein blindes Akzeptieren.
- Der private Key wird mit Dateirechten `600` gespeichert.
- Passwörter werden nur für die initiale Einrichtung verwendet und nicht persistiert.

---

## Beenden

`Ctrl+C` stoppt den Observer sauber:
```
2026-03-20 14:45:00 - INFO - Beende Ueberwachung...
2026-03-20 14:45:00 - INFO - SecureSync gestoppt.
```
