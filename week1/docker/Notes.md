# Setting up Environment on Google Cloud (Cloud VM + SSH)

The following outlines the steps to configure a Google Cloud VM.

## Create an SSH key pair
Create .ssh directory `mkdir ~/.ssh ` if it doesn't already exist. Then, generate an SSH key pair by running the following command in the terminal: 

```bash
    cd ~/.ssh
    bash ssh-keygen -t rsa -f KEY_FILENAME -C USERNAME
```
You'll be prompted with serveral questions, press enter three times to confirm selections. 

This will generate a public (gcp.pub) and private key (gcp) used for secure SSH access. Open the gcp.pub file using `cat gcp.pub ` command and copy its contents. 

Using GCP console, paste the contents of the key into the SSH key text box under the Metadata tab. Now, you can connect to your Cloud VM instance from your local machine using the command:

`ssh -i ~/.ssh/privateKey_Filename user@external IP`

## Configure VM instance in GCP
In the GCP Console, create a new VM instance. Configure the following settings:
- Name, Region, Series, and Machine Type
- Boot Disk: Select Ubuntu 20.04 LTS, choose Balanced persistent disk, and set the Size to 30 GB

All other settings can be left at their default values.

#### Connect SSH to VM instance

Run the below to connect SSH to your new machine:

`ssh -i ~/.ssh/privateKey_Filename user@external IP `

Where external IP is your VMs External IP, located in your gcp console.

### Optional: Configure a SSH alias

To easily connect to machine from terminal, make a configuration file to host your server details.

1. Change into SSH directory with command:
`~/.ssh`

2. Create a new file

Within same directory, `nano config` to create the new file.

3. Create configuration

Host host
    HostName hostname
    User user
    IdentityFile ~/.ssh/key_file

(Note: The HostName, User, and IdentityFile commands must be indented.)

4. SSH into vm instance with command `ssh hostname`

## Configure VM and Setup local environment

Here we will be installing Anaconda, Docker, Docker-Compose, PgCli and clone any git repos, necessary for this course.

### Anaconda - Download and Run the file
```bash wget https://repo.anaconda.com/archive/Anaconda3-2022.10-Linux-x86_64.sh 
    bash Anaconda3-2022.10-Linux-x86_64.sh 
```
When prompted, enter `yes` to run `conda init`. Then, execute `source .bashrc ` to apply changes made to your `bash .bashrc` file. Alternatively, you can apply changes by logging out of the terminal session and SSHing back into the machine.

Use the command `which python` to confirm that Python is installed and that Anaconda is the active environment.

### Docker - Install and Run

The following commands install Docker:

```bash 
sudo apt-get update
sudo apt-get upgrade
sudo apt-get install docker-io
```

Since we're using sudo, you may encounter a 'permission denied' error. To avoid this and run Docker without sudo, follow these steps:

```bash
sudo groupadd docker
sudo gpasswd -a $USER docker
sudo service docker restart
```

To confirm Docker installation, log out, log back in, and execute `docker run hello-world`.

### Docker-Compose - Download latest release and Run

Create a new `bin` folder in VM instance and download.

`wget https://github.com/docker/compose/releases/download/v2.35.0/docker-compose-linux-x86_64 -O docker-compose`

After manually downloading the file, we need to mark it as executable so the system can run it.

`chmod +x docker-compose`

Now, add the bin directory to your system's PATH, append the following ling to the end of .bashrc `echo 'export PATH="${HOME}/bin:${PATH}"' >> ~/.bashrc`

This will ensure that any executable in the `~/bin` directory are included in your system's PATH. Run `source ~/.bashrc` to apply the changes.

### PgCli - Install and Connect

``` pip install pgcli ```

Connect to postgres database using the command:
`pgcli -h hostname -u username -d database-name`

#### Optional: Setup port forwarding in VS Code to connect to pgAdmin and Jupyter

In Visual Studio Code, go to the Ports tab and add a new port by setting up port forwarding. By forwarding a port from the remote server, VS Code allows local access to services like PostgreSQL, making them behave as though they’re running on your own machine.

In this case, we’re adding the PostgreSQL, pgAdmin and Jupyter Notebook (see below) ports as listed in the output of the `docker ps` command. Navigate to `http://localhost:8080/` and login into pgAdmin. 

#### Run Jupyter to run ny_taxi_data notebook

Navigate to where ny_taxi_data.ipynb is located on the remote VM, then run jupyter server: `jupyter notebook`. This will launch Jupyter Notebook and allow you to open and run the notebook in your browser.

** This didn't initially work for me because applications were already running on port 8888. As a workaround, I identified the process using the port with: `lsof -i :8888` and terminated the process `kill -9 <PID>` on my local and remote machines. 

** Make sure the ingestion Jupyter notebook is also on the remote server. I initially made the mistake of cloning most project files except this one.

To copy a file from local machine to VM, use the `scp` command:
`scp /path/to/local/ingest_file.ipynb username@vm_external_ip:/path/on/vm`

### Terraform - Install and Run





