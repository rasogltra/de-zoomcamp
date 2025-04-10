## Setting up Environment on Google Cloud (Cloud VM + SSH)

### Create an SSH key pair

Create .ssh directory, if not exists. Run below ```bash ssh-keygen``` command in terminal to create a SSH key pair.

```bash ssh-keygen -t rsa -f ~/.ssh/KEY_FILENAME -C USERNAME ```

This command generates a public and private key.

Using GCP console, add public SSH key to project metadata.

### Configure VM instance in GCP

In GCP console, create and configure VM instance. (note: this project uses the Ubuntu 20.4 disk environment). 

#### Connect SSH to VM instance

Run the below to connect SSH to your new machine:

```bash ssh -i ~/.ssh/privateKey_Filename user@external IP ``

Where external IP is your VMs External IP, located in your gcp console.

#### Use a SSH Config File for Easier Connection to machine

To easily connect to machine from terminal, make a configuration file to host your server details.

1. Change into SSH directory with command:
```bash ~/.ssh```

2. Create a new file

Within same directory, ```bash nano config ``` to create the new file.

3. Create configuration
Example: 

Host myfirst_cloud
HostName 192.168.1.20
User lugi
IdentityFile ~/.ssh/id_rsa

4. SSH into machine with command ```bash ssh myfirst_cloud```

### Configure VM and Setup local environment

#### Install

Within machine, install Anaconda, Docker, Docker-Compose and clone any git repos. (note: add packages to path)

```bash wget https://github.com/docker/compose/releases/download/v2.35.0/docker-compose-linux-x86_64 -O docker-compose ```




