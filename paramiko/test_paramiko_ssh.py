import paramiko
import os
from dotenv import load_dotenv

# Load environment variables from the .env file in the project root
load_dotenv()

# --- CONFIGURATION FROM ENVIRONMENT ---
# These values are pulled from your local .env file (secured by .gitignore)
SSH_HOST = os.getenv("SSH_HOST")
SSH_USER = os.getenv("SSH_USER")
SSH_KEY_NAME = os.getenv("SSH_KEY_NAME", "github") # Defaults to 'github'

# --- CROSS-PLATFORM PATHS ---
# Build the path to your private SSH key dynamically
PRIVATE_KEY_PATH = os.path.expanduser(os.path.join("~", ".ssh", SSH_KEY_NAME))

def connect_and_upload():
    # Validation: Ensure essential credentials were loaded
    if not SSH_HOST or not SSH_USER:
        print("❌ Error: SSH_HOST or SSH_USER not found in .env file.")
        return False

    # Define local and remote directories
    local_dir = os.path.expanduser(os.path.join("~", "projects", "FWH-SecureSync", "paramiko", "transfer_test"))
    remote_dir = f"/home/{SSH_USER}/uploads"

    client = paramiko.SSHClient()
    # Automatically add the server's host key (standard for private lab environments)
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # Verify that the SSH key exists locally
        if not os.path.exists(PRIVATE_KEY_PATH):
            print(f"❌ Error: Private key not found at: {PRIVATE_KEY_PATH}")
            return False

        print(f"--- Connecting to {SSH_HOST} as {SSH_USER} ---")
        
        # Establish connection using the private key
        client.connect(
            hostname=SSH_HOST, 
            username=SSH_USER, 
            key_filename=PRIVATE_KEY_PATH,
            timeout=10
        )
        
        print("✅ Connection successful: Credentials loaded from environment.")

        sftp = client.open_sftp()
        
        if not os.path.exists(local_dir):
            print(f"❌ Local directory {local_dir} not found.")
            return False

        # List all files in the local directory
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
    connect_and_upload()