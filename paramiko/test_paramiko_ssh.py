import paramiko
import os

# Authentication for the Debian server
SSH_HOST = "192.168.2.124"
SSH_USER = "securesync"

# --- CROSS-PLATFORM KEY PATH ---
# os.path.expanduser("~") finds the correct home directory on ANY OS.
PRIVATE_KEY_PATH = os.path.expanduser(os.path.join("~", ".ssh", "github"))

def connect_to_server():
    # --- CROSS-PLATFORM LOCAL DIRECTORY ---
    # Using join ensures the slashes ( / vs \ ) are correct for the OS
    local_dir = os.path.expanduser(os.path.join("~", "projects", "FWH-SecureSync", "paramiko", "transfer_test"))
    remote_dir = f"/home/{SSH_USER}/uploads"

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # Check if the private key exists before attempting connection
        if not os.path.exists(PRIVATE_KEY_PATH):
            print(f"❌ Error: SSH Key not found at: {PRIVATE_KEY_PATH}")
            print("💡 Make sure your 'github' key is in the .ssh folder of your home directory.")
            return False

        print(f"--- Connecting to {SSH_HOST} ---")
        print(f"--- Using Key: {PRIVATE_KEY_PATH} ---")
        
        client.connect(
            hostname=SSH_HOST, 
            username=SSH_USER, 
            key_filename=PRIVATE_KEY_PATH,
            timeout=10
        )
        
        print("✅ Connection established: Platform-independent authentication successful.")

        sftp = client.open_sftp()
        
        # Check if local directory exists
        if not os.path.exists(local_dir):
            print(f"❌ Local directory {local_dir} not found.")
            return False

        files = [f for f in os.listdir(local_dir) if os.path.isfile(os.path.join(local_dir, f))]

        if not files:
            print("ℹ️ No files found to upload.")
        else:
            for file_name in files:
                local_path = os.path.join(local_dir, file_name)
                remote_path = f"{remote_dir}/{file_name}"
                sftp.put(local_path, remote_path)
                print(f"🚀 Uploaded: {file_name}")

        sftp.close()
        return True

    except Exception as e:
        print(f"❌ Connection failed: {e}")
    finally:
        client.close()
        print("--- Session finished ---")

if __name__ == "__main__":
    connect_to_server()