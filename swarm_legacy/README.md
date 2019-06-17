# Legacy Docker Swarm
## Setup
We follow [Andrea Zonca's guide](https://zonca.github.io/2016/05/jupyterhub-docker-swarm.html) for setting up JHub and [DockerSpawner](https://github.com/jupyterhub/dockerspawner) to spawn notebook server containers in a <i>legacy</i> Docker swarm.
At the time of this writing, there aren't yet good ways to handling the new swarm mode that's integrated into the Docker engine.
This is probably going to be fixed in the future, but for now, it should provide a (stable) way to use Docker swarm.
Documentation for <i>legacy</i> Docker swarm can be found [here](https://docs.docker.com/swarm/overview/).

1. We'll need to create a new security group under EC2:
  (I don't think that we are using the swarm manager? Seems that we combined the manager with the hub, but we should also have more than one manager) We create another security group named "Swarm manager" that has the following ports open to the VPC. Leave the outbound ports as default and add the following custom inbound port rules:
  
      |Ports |	Protocol	| Source |
      |------|----------|--------|
      |2375	| tcp	| 172.31.0.0/16 |
      |4000	| tcp	| 172.31.0.0/16 |
      |8500| tcp	| 172.31.0.0/16 |
      |32000-33000| tcp	| 172.31.0.0/16 |

   We make a final security group named "Swarm Worker". Leave the outbound ports as default and add the following custom inbound port rules:
   
      |Ports |	Protocol	| Source |
      |------|----------|--------|
      |All TCP	| tcp	| 172.31.0.0/16 |
      |22	| tcp	| 172.31.0.0/16 |
      |22 | tcp	| 172.31.0.0/16 |

2. Create two amazon ami t2.xlarge worker instances, or however many you will need given the amount of students and attach the security group to them. Be aware that the data8 notebooks are 4gb large, so nothing smaller than a t2.large will allow you to build the notebooks.
 
3.Install Docker on both the jupyterhub and worker instances:
   ```bash
   sudo yum -y update
   curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.rpm.sh | sudo bash
   sudo yum -y install docker git git-lfs
   sudo vim /etc/sysconfig/docker
      # Add OPTIONS = "...  -H tcp://0.0.0.0:2375 -H unix:///var/run/docker.sock"
   sudo service docker start
   sudo usermod -aG docker ec2-user
   logout
   ```

   Logout and then log back in to propagate the group change.

4. Set up NFS on both Jupyterhub and worker instances [NFS stuff](../nfs/README.md).

5. Clone this repo if you haven't already:
   ```bash
   cd && mkdir repos && cd repos
   git clone https://github.com/jamesfolberth/stem-camp-deploy.git
   ```

   Build the notebook image
   ```bash
   cd ~/repos/stem-camp-deploy/data8-notebook
   ./build.sh
   ```

   Alternatively, you can pull the latest version of data8-notebook from Docker hub.
   ```bash
   cd ~/repos/stem-camp-deploy/data8-notebook
   ./pull.sh
   ```
   This will pull jamesfolberth/data8-notebook:latest and tag it as data8-notebook.


   If we're a manager, start with the `start_manager.sh` script.
   ```bash
   cd ~/repos/stem-camp-deploy/swarm_legacy
   ./start_manager.sh
   ```

   If we're a worker, start with the `start_worker.sh` script.
   I'm not sure it's strictly necessary, but it's potentially wise/better to ensure the manager is already running.
   ```bash
   cd ~/repos/stem-camp-deploy/swarm_legacy
   ./start_worker.sh {LOCAL_IPv4_OF_MANAGER}
   ```

   You can get the local IP of the manager instance by running `ec2-metadata` on the manager node or looking in the AWS console.

6.  This should get everything set up.

## Some Helpful Commands
Here are some useful docker commands

```
# What's running on the local machine?
docker ps -a

# What's running in the swarm?  (run on the manager)
docker -H :4000 ps -a

# Information about the state of the swarm?  (run on the manager)
docker -H :4000 info
```

If you want to shut down a worker instance, I'd follow these steps:
* Run `docker -H :4000 ps -a` on the manager node to see which containers are running on the worker you want to shut down.
* From the Jupyterhub Admin page, shut down those containers (or ask the users to shut them down and log out of their single-user notebook servers).
* Stop the swarm image on the worker, which will let the worker leave.
  Note that it may take a minute or two for `docker -H :4000 info` to reflect the lost worker.
* It should be safe to shut down the worker.
