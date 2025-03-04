# Intention

Having multiple, special configured linux systems, in case of a system crash it take a lot of time to recover the system. Where are any tools, that can backup files and folders, but not the whole system at once. True, PROXMOX can do that, but not for raspberian - for example.

## How it works

The machine, we like to backup have to be added into a list for further processing. 
For the automated backup process, we need a ssh key on that machine. The backup process log in the machine, select the boot image, call "dd" to copy the disk image, zip that data and use a netcat session to transport the data to the backup host. On the backup host an *.img.gz is written.  
This image can be used to recover the system at once and restart the whole machine in that configuration.
Only the boot image will be backed up, not additionally, external disks.
The Webserver itself is based on a simple flask server and using the free "Mobirise Website Builder" for design elements. 


## How to to use

....