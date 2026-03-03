# paramiko-DOKU

## 25.02.2026 - add SSH authentication (key/password) 

## 26.02.2026 - implement connection testing and error handling 

## 27.02.2026 - create folder "transfer_test" in ~/projects/FWH-SecureSync/paramiko/transfer_test

## 01.03.2026 - add SFTP file transfer functionality

## security - switch to ssh key authentication
 Description: Remov password-based login. The script now uses the existing 'github' SSH key for secure passwordless authentication

## 02.03.2026 
- implement encrypted credential storage
- Move sensitive host data to .env and update script to use python-dotenv. Add .gitignore to protect secrets.

## implement logging system 
(~/projects/FWH-SecureSync/transfer.log)