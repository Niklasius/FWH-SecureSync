import paramiko
import os
import sys       # Allows a clean exit of the program in case of errors

# Authentication for the Debian server
SSH_HOST = "192.168.2.124"  # The IP address of the Debian VM
SSH_USER = "securesync"     # The user created during installation
SSH_PASS = "Pa$$w0rd"       # The corresponding password

def connect_to_server():
    # This function establishes an encrypted connection to the server,
    # checks a local folder, and uploads any existing files.
    
    # --- PATH CONFIGURATION ---
    # expanduser converts '~' into the full path (e.g., /Users/username/...)
    local_dir = os.path.expanduser("~/projects/FWH-SecureSync/paramiko/transfer_test")
    remote_dir = f"/home/{SSH_USER}/uploads"

    # 1. Create SSH client object:
    # Think of it as the 'telephone' used to call the server.
    client = paramiko.SSHClient()
    
    # 2. Set security policy:
    # AutoAddPolicy() says: 'Yes, automatically add the server key.'
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # VERIFICATION: Does the local folder exist at all?
        if not os.path.exists(local_dir):
            print(f"❌ Error: Local folder {local_dir} does not exist.")
            return False

        print(f"--- Starting connection setup to {SSH_HOST} ---")
        
        # 3. (Login):
        client.connect(
            hostname=SSH_HOST, 
            username=SSH_USER, 
            password=SSH_PASS, 
            timeout=10
        )
        
        print("✅ Authentication successful: The door is open.")

        # 4. Execute a command on the remote system:
        # exec_command sends the string directly to the Debian bash.
        stdin, stdout, stderr = client.exec_command('uptime')
        output = stdout.read().decode('utf-8').strip()
        print(f"🐧 Message from Debian server: {output}")

        # --- 5. SFTP Subsystem for file transfer ---
        print(f"📁 Searching for files in {local_dir}...")
        sftp = client.open_sftp()

        # Listing all files in the local directory
        files = [f for f in os.listdir(local_dir) if os.path.isfile(os.path.join(local_dir, f))]

        if not files:
            print("ℹ️ No files found in local folder for upload.")
        else:
            for file_name in files:
                local_path = os.path.join(local_dir, file_name)
                remote_path = f"{remote_dir}/{file_name}"
                
                print(f"🚀 Transferring: {file_name} ...")
                sftp.put(local_path, remote_path)
                print(f"✅ {file_name} successfully uploaded to {remote_dir}.")

        sftp.close()
        return True

    except paramiko.AuthenticationException:
        # Occurs if username or password is incorrect.
        print("❌ Login Error: Check user and password in the Debian VM.")
    except paramiko.SSHException as e:
        # Occurs if there are issues with the SSH protocol.
        print(f"❌ SSH Protocol Error: {e}")
    except Exception as e:
        # Catches all other errors (e.g., wrong IP or 'server is down').
        print(f"❌ Network Error: {e}")
    finally:
        # 6. Cleanly disconnect:
        # This is extremely important to prevent 'dead' sessions on the server.
        client.close()
        print("--- Connection closed and resources released ---")
        return False

if __name__ == "__main__":
    connect_to_server()