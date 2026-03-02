# paramiko-DOKU

# 25.02.2026
# added SSH authentication (key/password) 

# 26.02.2026
# implemented connection testing and error handling 

# 27.02.2026
# created folder "transfer_test" in ~/projects/FWH-SecureSync/paramiko/transfer_test

# 01.03.2026
# add SFTP file transfer functionality

#  security: switch to ssh key authentication
# Description: Removed password-based login. The script now uses the existing 'github' SSH key for secure passwordless authentication

# 02.03.2026 
# implement encrypted credential storage
# Moved sensitive host data to .env and updated script to use python-dotenv. Added .gitignore to protect secrets.