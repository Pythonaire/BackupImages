# Intention

Having multiple, special configured server, in case of system crash it take a lot of tine to recover. I found any tools, that can backup files and folders, but not the whole system at once. True, PROXMOX can do that, but not for raspberian for example.

## How it works

The machine, we like to backup have to be added into a list for further processing. 
For the automated backup process, we need a ssh key on that machine. The backup process log in the machine, call dd to copy the disk image, zip that data and use netcat session to transport the data to the backup host. On the backup host an *.img.gz is written.  
Web Webserver itself is based on a simple flask server and using the free 2Mobirise Website Builder" for design elements. 

## How to to use

....