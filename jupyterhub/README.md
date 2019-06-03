# Jupyterhub Instance

The Jupyterhub instance will run Jupyterhub behind nginx, which we will use as a proxy server.
It will also run the Docker Swarm manager (container), which will connect Jupyterhub to the worker nodes.
For now, let's get the server (an AWS EC2 instance) up and running, and install Jupyterhub.


1. Starting the hub/webserver/Swarm manager instance
   * (Choose AMI and instance type) We used a standard 64-bit(x86) Amazon Linux AMI on a t2.micro instance for testing, however a larger instance is recommended for the actual build. May need to install a few more packages with `pip` and `conda`.
   * (configure instance and storage and tags?) 
   * (configure security groups) 
     We're running all instances in the same AWS virtual private cloud (VPC).
     Suppose our VPC's IPv4 CIDR is 172.31.0.0/16.
     
     We create a new security group called "jhub" with the following custom ports:

        |Type  | Ports |Protocol | Source |
        |------|-------|---------|-------|
        |SSH   | 22	   | tcp	   | 0.0.0.0/0, ::/0 | 
        |HTTP  | 80	   | tcp 	   | 0.0.0.0/0, ::/0 |
        |HTTPS | 443   | tcp	   | 0.0.0.0/0, ::/0 |
        |All traffic| All | All  | (the CIDR address for your VPC) |

    * (where is this configured? I can't find this security group) For inside the VPC only, we add the following ports to allow the hub API and connect to the notebooks on remote nodes.

        |Ports |	Protocol	| Source |
        |------|----------|--------|
        |8081| tcp	| 172.31.0.0/16 |
        |32000-33000| tcp	| 172.31.0.0/16 |

        Later on we'll use this node as a Docker swarm manager, which will require a few more open ports inside the VPC.
        See [Docker Swarm manager and workers](../swarm_legacy/README.md) for details.

    * Since we're inside a VPC (i.e., closed off from the outside world except for the above ports), we can instead just enable all ports 0-65536 for 172.31.0.0/16, which is the CIDR of the default VPC.
  
    * You will need to create or enter a SSH Key to launch the instance, make sure to put the pem file in your ~/.ssh folder and that you change the permissions of the file using:
    chmod 400 <your-key.pem>
    
    * Return to the EC2 menu and wait for the instance to finish building. 
    
2. Connect to the EC2 instance and install a bunch of packages
   * To connect to the new instance, you'll need your SSH private key.
    
   * connect to your ec2 instance by opening a terminal(for mac or linux) and typing 
     `ssh -i ~/.ssh/<aws_key.pem> ec2-user@<PUBLIC_IPv4>`.
     ( your IP address is located on the description of your ec2 instance )
     The standard user is `ec2-user`, which has `sudo` privileges; once inside, you can make new users and add other authorized SSH keys if you like.
     We'll use `ec2-user2` to orchestrate everything.

     **Protip**: add the following function/alias to your `.bashrc`, so you can `aws-ssh <PUBLIC_IPv4>`.
     If you have an elastic IP or a domain name to use, you can also edit your `~/.ssh/config`.
     
     ~/.bashrc:
     ```bash
     aws-ssh() {
         ssh -i ~/.ssh/<aws_key.pem> ec2-user@$1
     }
     ```

   * Make a directory for Jupyterhub server files (e.g., SSL certs, user list)
      ```bash
      sudo mkdir -p /srv/jupyterhub
      sudo chown -R ec2-user:ec2-user /srv/jupyterhub/
      chmod -R 700 /srv/jupyterhub
      ```

   * Install a repo and docker, then start docker:
      ```bash
      sudo yum update -y
      curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.rpm.sh | sudo bash
      sudo amazon-linux-extras install epel
      sudo yum install -y python36 python36-pip python36-devel git git-lfs docker gcc gcc-c++
      sudo service docker start
      ```

   * Clone the stem-camp-deploy repo
      ```bash
      cd && mkdir repos && cd repos
      git clone https://github.com/jamesfolberth/stem-camp-deploy.git
      ```

   * Add `ec2-user` to the Docker group, so we don't have to `sudo` every time we want to run a Docker container.
      ```bash
      sudo usermod -aG docker ec2-user
      ```

   * Logout and back in to make group changes for `ec2-user`.
     Verify that ec2-user is listed when running command `groups`.

   * Verify docker works with `docker run hello-world`.

   * Download and install Node.js, which provides npm.
     You probably want to visit [nodejs.org](https://nodejs.org/en/download/) to look up the latest LTS version.(search for the 64-bit linux version and replace the <vx.xx.xx> with the most recent version number)

     ```bash
     cd && mkdir downloads && cd downloads

     wget https://nodejs.org/dist/<vX.XX.XX>/node-<vX.XX.XX>-linux-x64.tar.xz
     tar -xvf node-<vX.XX.XX>-linux-x64.tar.xz
     cd node-<vX.XX.XX>-linux-x64.tar.xz
     sudo cp -r bin/* /usr/bin/
     sudo cp -r include/* /usr/include/
     sudo cp -r lib/* /usr/lib/
     sudo cp -r share/* /usr/share/
     cd ..
     ```

   * Install [configurable-http-proxy](https://github.com/jupyterhub/configurable-http-proxy), which is needed by Jupyterhub.
     ```bash
     sudo npm install -g configurable-http-proxy
     ```

   * Install python packages with `pip`.
     ```bash
     pip install jupyterhub --user
     pip install --upgrade notebook
     pip install oauthenticator dockerspawner --user
     ```

3. Set up Jupyterhub
    * Add at least one admin user to `/srv/jupyterhub/userlist` with the following format
        ```
        user.name@gmail.com admin
        ```
      This user will add other users through the web interface.
      We have callbacks set up in `my_oauthenticator.py` that should automagically get things set up, which includes

      1. Creating a system user on the Jupyterhub machine
      2. Creating a home directory for that user on the NFS-mounted EFS (mounted on `/mnt/nfs/home`)
      3. `rsync`ing the notebooks from this repo into the user's home directory.

    * If you have the [nginx](../nginx/README.md) and the [NFS mount](../nfs/README.md) set up, you can try starting Jupyterhub.

      But...
      - if authentication failed (e.g., user not in `/srv/jupyterhub/userlist` or user not added through Jupyterhub web interface by admin user), you should see a 403 "Forbidden".
      - we haven't built/pulled the data8-notebook (see [data8-notebook README](../data8-notebook/README.md)) or started the Docker swarm manager/workers, so if you try to start a server, you should see a 500 "Internal Server Error".

4. Set up [nginx](../nginx/README.md), [NFS](../nfs/README.md), and set up the [Docker swarm](../swarm_legacy/README.md).

5. Start Jupyterhub

    This should be as simple as running `start.sh`.
    I like to run `start.sh` in a `screen` session so I can detach and logout of my SSH connection.
