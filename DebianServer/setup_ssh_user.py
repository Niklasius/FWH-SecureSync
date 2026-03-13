"""
setup_ssh_user.py
-----------------
Verbindet sich mit einem Ubuntu-Server, erstellt einen neuen Benutzer,
generiert ein SSH-Key-Paar und hinterlegt den Public Key auf dem Server.

Voraussetzungen:
    pip install paramiko

Ausführung (PowerShell):
    python setup_ssh_user.py
"""

import paramiko
import os
import sys
import getpass


def run(client: paramiko.SSHClient, command: str, check: bool = True) -> str:
    stdin, stdout, stderr = client.exec_command(command)
    exit_code = stdout.channel.recv_exit_status()
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()

    if check and exit_code != 0:
        print(f"\n[FEHLER] Befehl fehlgeschlagen (Exit {exit_code}): {command}")
        if err:
            print(f"         Stderr: {err}")
        sys.exit(1)

    return out


def generate_key_pair(key_name: str):
    key = paramiko.RSAKey.generate(4096)

    ssh_dir = os.path.expanduser("~/.ssh")
    os.makedirs(ssh_dir, exist_ok=True)
    private_key_path = os.path.join(ssh_dir, key_name)

    if os.path.exists(private_key_path):
        print(f"\n[WARNUNG] Datei existiert bereits: {private_key_path}")
        overwrite = input("         Überschreiben? (j/N): ").strip().lower()
        if overwrite != "j":
            print("Abgebrochen.")
            sys.exit(0)

    key.write_private_key_file(private_key_path)

    try:
        os.chmod(private_key_path, 0o600)
    except Exception:
        pass

    public_key_str = f"{key.get_name()} {key.get_base64()} {key_name}"
    return key, private_key_path, public_key_str


def create_user(client: paramiko.SSHClient, username: str, password: str):
    exists = run(client, f"id -u {username} 2>/dev/null || echo 'notfound'", check=False)
    if exists != "notfound":
        print(f"[INFO] Benutzer '{username}' existiert bereits – Key wird trotzdem hinterlegt.")
        return

    print(f"[...] Erstelle Benutzer '{username}' ...")
    run(client, f"useradd -m -s /bin/bash {username}")

    stdin, stdout, stderr = client.exec_command("chpasswd")
    stdin.write(f"{username}:{password}\n")
    stdin.flush()
    stdin.channel.shutdown_write()
    stdout.channel.recv_exit_status()

    print(f"[OK]  Benutzer '{username}' erstellt.")


def deploy_public_key(client: paramiko.SSHClient, username: str, public_key_str: str):
    ssh_dir = f"/home/{username}/.ssh"

    print("[...] Hinterlege Public Key auf dem Server ...")
    run(client, f"mkdir -p {ssh_dir}")
    run(client, f"chmod 700 {ssh_dir}")

    key_b64 = public_key_str.split()[1]
    check = run(client, f"grep -q '{key_b64}' {ssh_dir}/authorized_keys 2>/dev/null && echo 'exists' || echo 'new'", check=False)

    if check == "exists":
        print("[INFO] Public Key ist bereits in authorized_keys eingetragen.")
    else:
        run(client, f"echo '{public_key_str}' >> {ssh_dir}/authorized_keys")

    run(client, f"chmod 600 {ssh_dir}/authorized_keys")
    run(client, f"chown -R {username}:{username} {ssh_dir}")
    print("[OK]  Public Key hinterlegt.")


def verify_connection(hostname: str, port: int, username: str, private_key_path: str):
    print(f"\n[...] Teste Verbindung als '{username}' mit SSH-Key ...")
    key = paramiko.RSAKey.from_private_key_file(private_key_path)
    test_client = paramiko.SSHClient()
    test_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        test_client.connect(hostname, port=port, username=username, pkey=key, timeout=10)
        whoami = run(test_client, "whoami")
        print(f"[OK]  Verbindung erfolgreich! Eingeloggt als: {whoami}")
    except Exception as e:
        print(f"[FEHLER] Verbindungstest fehlgeschlagen: {e}")
    finally:
        test_client.close()


def main():
    print("=" * 55)
    print("  Ubuntu User + SSH-Key Setup")
    print("=" * 55)

    # ── Server ────────────────────────────────────
    print("\n--- Server ---")
    host = input("IP-Adresse oder Hostname: ").strip()
    if not host:
        print("[FEHLER] Adresse darf nicht leer sein.")
        sys.exit(1)

    port_input = input("SSH-Port (Standard: 22): ").strip()
    port = int(port_input) if port_input else 22

    # ── Admin-Zugangsdaten ────────────────────────
    print("\n--- Root / Admin-Zugang ---")
    admin = input("Benutzername: ").strip()
    if not admin:
        print("[FEHLER] Admin-Benutzername darf nicht leer sein.")
        sys.exit(1)
    admin_pass = getpass.getpass("Passwort: ")

    # ── Neuer Benutzer ────────────────────────────
    print("\n--- Neuer Benutzer ---")
    new_user = input("Benutzername: ").strip()
    if not new_user:
        print("[FEHLER] Benutzername darf nicht leer sein.")
        sys.exit(1)

    new_pass = getpass.getpass("Passwort: ")
    new_pass_confirm = getpass.getpass("Passwort bestätigen: ")
    if new_pass != new_pass_confirm:
        print("[FEHLER] Passwörter stimmen nicht überein.")
        sys.exit(1)

    key_name = input(f"Name der Key-Datei (Standard: {new_user}_rsa): ").strip() or f"{new_user}_rsa"

    # ── Mit Server verbinden ──────────────────────
    print(f"\n[...] Verbinde mit {host}:{port} als '{admin}' ...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        client.connect(host, port=port, username=admin, password=admin_pass, timeout=15)
    except Exception as e:
        print(f"[FEHLER] Verbindung fehlgeschlagen: {e}")
        sys.exit(1)

    print("[OK]  Verbunden.\n")

    # ── Benutzer erstellen ────────────────────────
    create_user(client, new_user, new_pass)

    # ── SSH-Key-Paar generieren ───────────────────
    print(f"[...] Generiere RSA-4096-Key-Paar ...")
    key, private_key_path, public_key_str = generate_key_pair(key_name)
    print(f"[OK]  Privater Key gespeichert unter: {private_key_path}")

    # ── Public Key auf Server hinterlegen ─────────
    deploy_public_key(client, new_user, public_key_str)
    client.close()

    # ── Verbindung testen ─────────────────────────
    verify_connection(host, port, new_user, private_key_path)

    # ── Zusammenfassung ───────────────────────────
    print("\n" + "=" * 55)
    print("  Fertig!")
    print("=" * 55)
    print(f"  Server:       {host}:{port}")
    print(f"  Benutzer:     {new_user}")
    print(f"  Privater Key: {private_key_path}")
    print()
    print("  Verbinden mit:")
    print(f"  ssh -i {private_key_path} {new_user}@{host}")
    print("=" * 55)


if __name__ == "__main__":
    main()
