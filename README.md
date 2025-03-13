# Intention

Having multiple, special configured linux systems, in case of a system crash it take a lot of time to recover the systems from the scratch, with all configurations, packages etc. Where are any tools (like "Time Shift"), that can backup files and folders, but not the whole system at once. True, PROXMOX can do that, but not for raspberian - for example. Along this small web server, we can run multiple backup processes in parallel and generate images from all linux systems inside our local network.  

## How it works

Having the web server, the machine, we like to backup, have to be added into a list for further processing. The server check the ability of the host we adding, then store the hosts in UNIX_System.json with ip address, username and the detected boot disk.  
For the automated backup process, we need a ssh key on that machine. The backup process log in the machine, select the boot image, call "dd" to copy the disk image, zip that data and use a netcat session to transport the data to the backup host. On the backup host an *.img.gz is written.  
This image can be used to recover the system at once and restart the whole machine in that configuration.
Only the boot image will be backed up, not additionally, external disks.
The web server itself is based on a simple flask server and using the free "Mobirise Website Builder" for design elements. 


## How to to use

1) To get the flask server running, generate a self signed certificate, use your own or remove ssl_context in flask definition main.py (without ssl http is needed instead of https):
````
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365
````
Store that certificate inside the static folder.
2) Make sure "paramiko", "flask" and "psutil" are installed
````
sudo pip install -r requirements.txt"
````
3) Make sure "netcat" and "gzip" are installed on the backup hosts and the backup client.
````
sudo apt install netcat gzip
````
4) Make sure, the user on the backup host and on the client side has the permission to execute netcat, dd and gzip, for example create a "backup_user" and use:
````
echo "<the user> ALL=(ALL) NOPASSWD: /bin/dd, /bin/nc" | sudo tee /etc/sudoers.d/<the user>
````
5) create a ssh key for the automated backup process on the backup hosts
````
ssh-keygen -t rsa -b 4096 -C "<the user>@<the server>" -f ~/.ssh/id_rsa -N ""
````
6) copy the generated ssh key to each backup client, you want to be backed up.
````
ssh-copy-id -i ~/.ssh/id_rsa.pub <the client user>@<client-ip>
````
On the client machine you should find ".ssh/authorized_keys" file. 

7) On the client machine allow the use of ssh certificates
````
sudo nano /etc/ssh/sshd_config
PubkeyAuthentication yes
AuthorizedKeysFile .ssh/authorized_keys

chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
````
8) restart ssh
````
sudo systemctl restart ssh
````
If you can login on that client "ssh '<the user>@<client ip>'" without the password, ssh via key works well. 

9) Start the web server via ```python main.py```or generate a systemctl. 

10) Use a web browser ```https://<your Backup Server>:<the flask port> ``` (predefined port is 5005, see main.py)

