# Intention

Having multiple, special configured linux systems, in case of a system crash it take a lot of time to recover the system. Where are any tools, that can backup files and folders, but not the whole system at once. True, PROXMOX can do that, but not for raspberian - for example.

## How it works

The machine, we like to backup have to be added into a list for further processing. 
For the automated backup process, we need a ssh key on that machine. The backup process log in the machine, select the boot image, call "dd" to copy the disk image, zip that data and use a netcat session to transport the data to the backup host. On the backup host an *.img.gz is written.  
This image can be used to recover the system at once and restart the whole machine in that configuration.
Only the boot image will be backed up, not additionally, external disks.
The Webserver itself is based on a simple flask server and using the free "Mobirise Website Builder" for design elements. 


## How to to use

1) To get the flask running, get a self signed certificate or use your own:
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

4) Make sure, the user on the backup host and the client has the permission to execute netcat, dd and gzip, for example create a "backup_user"
````
echo "<the user> ALL=(ALL) NOPASSWD: /bin/dd, /bin/nc" | sudo tee /etc/sudoers.d/<the user>
````
5) create a ssh key for the automated backup process on the backup hosts
````
ssh-keygen -t rsa -b 4096 -C "<the user>@<the server>" -f ~/.ssh/id_rsa -N ""
````
6) 
6) copy this ssh key to the backup client
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
If you can login on that client "ssh '<the user>@<client ip>'" without the password, it ssh works well with the ssh key. 

9) Use a Webbrowser https://<your Backup Server>:<the flask port> (predefined port 5005)

