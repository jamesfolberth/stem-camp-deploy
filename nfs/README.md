# NFS
We create an AWS EFS and mount it with NFS to use as the users' home directories.
This gives the users persistent storage within their Docker containers.
The EFS must be mounted on both the Jupyterhub/Docker swarm manager instance, and all Docker swarm worker instances.

1. On the AMI we used, `nfs-utils` is already installed.
   Otherwise, `sudo yum install nfs-utils` to install an NFS client.

2. We need to create a security group that opens up TCP 2409 inside the VPC, which is used by NFS clients.
   We're currently running security groups that are open on all ports inside the VPC.(seems that we ended up just using the same security group for jhub?)

3. Now create a new EFS. You can leave most of the options as default however make sure that you are assigning the correct security group to the VPC or the EFS won't mount. 

4. [EFS](http://docs.aws.amazon.com/efs/latest/ug/mount-fs-auto-mount-onreboot.html) gives us the mount command to use and also an entry for `/etc/fstab`.
   Put the following in `/etc/fstab` on each of the instances that will use nfs:

   ```
   ${mount-target-DNS}:/ ${efs-mount-point} nfs4 nfsvers=4.1,rsize=1048576,wsize=1048576,hard,timeo=600,retrans=2 0 0
   ```

   FS gives a `mount-target-DNS`('DNS name' listed under the 'EFS' details) that's something like `fs-XXXXXXX.efs.REGION.amazonaws.com`.
   We use `/mnt/nfs/home` for `efs-mount-point`.
   When the we run the Docker containers running Jupyter notebooks, we bind `/mnt/nfs/home` to `/home` inside the containers.


5. Create the mount point, mount the EFS, and restart the Docker daemon.

   ```bash
   sudo mkdir -p /mnt/nfs/home/
   sudo mount /mnt/nfs/home/
   sudo service docker restart
   ```
6. EFS is now set up. Return to the [Docker Swarm Readme](https://github.com/jamesfolberth/stem-camp-deploy/blob/ingoglia/swarm_legacy/README.md) to complete the rest of the setup.
