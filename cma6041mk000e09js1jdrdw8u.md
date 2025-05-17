---
title: "Setting Up Your Cloud Data Platform with Terraform"
datePublished: Thu May 01 2025 23:33:39 GMT+0000 (Coordinated Universal Time)
cuid: cma6041mk000e09js1jdrdw8u
slug: mastering-data-engineering-cloud
tags: vm, ssh, terraform, gcp, jupyter-notebook, sudo, portfowarding

---

This is my tech journal tracking a data engineering course with DataTalksClub: [**https://github.com/rasogltra/de-zoomcamp.git**.](https://github.com/rasogltra/de-zoomcamp.git)

Most of [module 1 was created on my local](https://github.com/rasogltra/de-zoomcamp.git) machine, this article will walk-through how to re-create those services on a Google Cloud virtual machine.

### **CONFIGURE A VM ON GOOGLE CLOUD (CLOUD + SSH)**

**CREATE A SSH KEY PAIR**

We created .ssh directory `mkdir ~/.ssh`, generated a ssh key pair and ran the `ssh-keygen` command in terminal. You’ll be prompted with several questions to confirm selections. This will generate a public (gcp.pub) and private key (gcp) used for our ssh access. We opened the public file, using `cat`[`gcp.pub`](http://gcp.pub) command and copied its contents.

```bash
cd ~/.ssh
ssh-keygen -t rsa -f KEY_FILENAME -C USERNAME
```

Within the GCP console, paste the key contents under the `Metadata` tab. Connect to the instance from your local machine.

```bash
ssh -i ~/.ssh/[key_file] [user]@[external IP]
```

**CONFIGURE GCP VM**

Within the GCP, we configured the settings:

* `Name`, `Region`, `Series` and `Machine Type`
    
* For `Boot Disk`: Select `Ubuntu 20.04 LTS`, `balanced persistent disk`, and size to `30 GB`.
    

All other settings were left to default values.

**CONNECT SSH TO VM**

```bash
ssh -i ~/.ssh/[Key_Filename] [user]@[external IP]
```

**OPTIONAL: CONFIGURE A SSH ALIAS**

To easily connect to machine from terminal, we made a configuration file that list server vm details by creating a config file within the `.ssh` directory. I learned that the HostName, User and IdentityFile must be indented or it won’t work. We can now ssh into the VM using the hostname `ssh hostname`.

```bash
Host host
    HostName hostname
    User user
    IdentityFile ~/.ssh/[key_file]
```

### **INSTALL PACKAGE LIBRARIES ON VM**

We installed Anaconda, Docker, Docker-Compose, pgCLI and cloned our project’s GitHub repo all necessary for the course to our remote server.

**ANACONDA - DOWNLOAD AND RUN THE FILE**

```bash
wget https://repo.anaconda.com/archive/Anaconda3-2022.10-Linux-x86_64.sh
```

and, then `bash Anaconda3-2022.10-Linux-x86_64.sh`. When prompted, I entered `yes` to run `conda init`. Then, execute `source .bashrc` to apply the changes. Alternatively, you can apply changes by logging out of the terminal session and ssh back into the machine. I used `which python` to confirm that python is installed and that Anaconda is the active environment.

**DOCKER - INSTALL AND RUN**

```bash
sudo apt-get update
sudo apt-get upgrade
sudo apt-get install docker-io
```

I encountered a `permission denied` error so to avoid this, I configured it to run without needing `sudo` and give me the permission to run Docker commands. To take effect, log out and log back in. I ran `docker run hello-world` to confirm everything works.

```bash
sudo groupadd docker
sudo gpasswd -a $USER docker
sudo service docker restart
```

**DOCKER-COMPOSE - DOWNLOAD AND RUN**

We created a `mkdir -p ~/bin` for the download and marked it as an executable so the system can run it.

```bash
wget https://github.com/docker/compose/releases/download/v2.35.0/docker-compose-linux-x86_64 -O docker-compose
```

```bash
chmod +x docker-compose
```

The bin directory was added to the system’s PATH, at the end of `.bashrc`. This ensures any executable in `~/bin` is included in my `$PATH` and to apply the changes, we ran `source ~/.bashrc`.

```bash
echo 'export PATH="${HOME}/bin:${PATH}"' >> ~/.bashrc
```

**PGCLI - INSTALL AND CONNECT**

I tested the connection using my database credentials from [module 1](https://hashnode.com/post/cma5uvq2u000208la0y8ybwok).

```bash
# install pgcli
pip install pgcli

# connect to the database
pgcli -h [hostname] -u [username] -d [database-name]
```

**OPTIONAL: SET-UP PORT FORWARDING IN VS CODE TO CONNECT TO PGADMIN AND JUPYTER**

In VS Code, under the Ports tab and we added a new port by setting up port forwarding. By forwarding a port from the remote server, VS Code allows local access to services like PostgreSQL, making them behave as though they’re running on your own machine. In this case, we’re adding Postgres, pgAdmin and Jupyter Notebook ports as listed in the output of the `docker ps` command.

**RUN JUPYTER ON DATA**

We changed directory to the Jupyter script in [module 1](https://hashnode.com/post/cma5uvq2u000208la0y8ybwok) within the virtual machine. I somehow did not clone the script to my remote server so I copied the file locally.

```bash
scp /path/to/local/ingest_data_file.ipynb [username]@vm_external_ip:/path/on/vm
```

I then ran the Jupyter server: `jupyter notebook`, which launches Jupyter Notebook to run the script. For some reason, this didn’t initially work for me because I had other applications running on port 8888. As a workaround, I identified the process using the `8888` port: `lsof -i :8888` and terminated the process `kill -9 <PID>` on my local and remote machines.

## **TERRAFORM**

**DOWNLOAD TERRAFORM**

The process to run Terraform was similar to how I installed the application on my local machine. We started by downloading the linux binary for Terraform inside the `bin` folder, from earlier.

```bash
wget https://releases.hashicorp.com/terraform/1.11.4/terraform_1.11.4_linux_amd64.zip
```

I also installed `unzip` to unzip the file.

```bash
sudo apt install unzip
unzip terraform_1.11.4_linux_amd64.zip
```

**CONFIGURE GOOGLE CLOUD (GCP) SERVICE ACCOUNT**

Like how we configured on my local machine, we needed to setup our `GOOGLE_APPLICATION_CREDENTIALS` remotely. It’s important to remember where you saved your `my-gcp-key.json` within your local Terraform folder, to copy it to your remote Terraform instance. I did create a `.gc` folder to store the key file remotely.

```bash
scp ~/terraform/[my-gcp-key.json] username@your-server-ip:~/.gc/
```

```bash
export GOOGLE_APPLICATION_CREDENTIALS=~/.gc/my-gcp-key.json
```

```bash
gcloud auth activate-service-account --key-file $GOOGLE_APPLICATION_CREDENTIALS
```

You should see a message saying the account was activated sucessfully. The creators of the Datacamp series used `sftp` instead of `scp`. If you're curious, check out this [Youtube Video](https://www.youtube.com/watch?v=ae-CV2KfoN0&list=PL3MmuxUbc_hJed7dXYoJw8DoCuVHhGEQb&index=14) where he walks-through that method.

**RUN TERRAFORM COMMANDS**

We’re ready to run the basic Terraform commands: `terraform init` and `terraform plan`. No need to run `terraform apply` at this point— we’ve already created buckets for this project in [module 1](https://hashnode.com/post/cma5uvq2u000208la0y8ybwok).

**SHUTDOWN AND REMOVE VM**

To shut down your virtual machine, you can either run `sudo shutdown now` in the terminal or use the Google Cloud Console to stop the instance manually by clicking the delete option.