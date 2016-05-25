Title: Jupyterhub deployment on multiple nodes with Docker Swarm
Date: 2016-05-24 12:00
Author: Andrea Zonca
Tags: ipython, jupyterhub, sdsc
Slug: jupyterhub-docker-swarm

This post is part of a series on deploying Jupyterhub on OpenStack tailored at workshops, in the previous posts I showed:

* [How to deploy a Jupyterhub on a single server with Docker and Python/R/Julia support](http://zonca.github.io/2016/04/jupyterhub-sdsc-cloud.html)
* [How to deploy the previous server from a pre-built image and customize it](http://zonca.github.io/2016/04/jupyterhub-image-sdsc-cloud.html)

The limitation of a single server setup is that it cannot scale beyond the resources available on that server, especially memory. Therefore for a workshop that requires to load large amount of memory or with lots of students it is recommended to use a multi-server setup.

Fortunately Docker already provides that flexibility thanks to [Docker Swarm](https://docs.docker.com/swarm/overview/). Docker Swarm allows to have a Docker instance that behaves like a normal single server instance but instead launches containers on a pool of servers. Therefore there are mininal changes on the Jupyterhub server.

## Setup the Jupyterhub server

Let's start from the public image already available, see just the first section "Create a Virtual Machine in OpenStack with the pre-built image" in http://zonca.github.io/2016/04/jupyterhub-image-sdsc-cloud.html for instructions on how to get the Jupyterhub single server running.

### Setup Docker Swarm

First of all we need to have Docker accessible remotely so we need to configure it to listen on a TCP port, edit `/etc/init/docker.conf` and replace `DOCKER_OPTS=` in the `start` section with:

    DOCKER_OPTS="-H tcp://0.0.0.0:2375 -H unix:///var/run/docker.sock"
    
Port 2375 is not open on the OpenStack configuration, so this is not a security issue.
    
Then we need to run 2 swarm services in Docker containers, first a distributed key-store listening on port 8500 that is needed for Swarm to store information about all the available nodes, Consul:

    docker run --restart=always  -d -p 8500:8500 --name=consul progrium/consul -server -bootstrap
    
the manager which provides the interface to Docker Swarm:

    docker run --restart=always  -d -p 4000:4000 swarm manage -H :4000 --replication --advertise LOCAL_HUB_IP:4000 consul://LOCAL_HUB_IP:8500
    
Replace `LOCAL_HUB_IP` with the internal ip of the instance, you can find it with `ifconfig` or from the OpenStack Instances dashboard.

We are running both with automatic restarting, so that they are launched again in case of failure or after reboot.

You can check if the containers are running with:

    docker ps -a
    
and then you can check if connection works with Docker Swarm on port 4000:

    docker -H :4000 ps -a
    
### Setup Jupyterhub

Following the work by Jess Hamrick for the [compmodels Jupyterhub deployment](https://github.com/compmodels/jupyterhub), we can get the `jupyterhub_config.py` and the `swarmspawner.py` files from https://gist.github.com/zonca/83d222df8d0b9eaebd02b83faa676753 and copy them into the home of the ubuntu user.

### Share users home via NFS

We have now a distributed system and we need a central location to store the home folders of the users, so that even if they happen to get containers on different server, they can still access their files.

Install NFS with the package manager:

    sudo apt-get install nfs-kernel-server

edit `/etc/exports`, add:

    /home    *(rw,sync,no_root_squash)

Ports are not open in the NFS configuration.

## Setup networking

Before preparing a node, create a new security group under Compute -> Access & Security and name it `swarm_group`.

We need to be able to have open traffic between the `swarmsecgroup` and the group of the Jupyterhub instance, `jupyterhubsecgroup` in my previous tutorial. So in the new `swarmsecgroup`, add this rule: 

   * Add Rule
   * Rule: ALL TCP
   * Direction: Ingress
   * Remote: Security Group
   * Security Group: `jupyterhubsecgroup`
   
Add another rule replacing Ingress with Egress.
Now open the `jupyterhubsecgroup` group and add the same 2 rules, just make sure to choose as target "Security Group" `swarmsecgroup`.

On the `swarmsecgroup` also add a Rule for SSH traffic from any source choosing CIDR and 0.0.0.0/0, you can disable this after having executed the configuration.
   
## Setup the Docker Swarm nodes

### Launch a plain Ubuntu instance

Launch a new instance, all it `swarmnode`, choose the size depending on your requirements, and then choose "Boot from image" and get Ubuntu 14.04 LTS. Remember to choose a Key Pair under Access & Security and assigne the Security Group `swarmsecgroup`.

Temporarily add a floating IP to this instance in order to SSH into it, see my first tutorial for more details.

### Setup Docker Swarm

First install Docker engine:

```
sudo apt update
sudo apt install apt-transport-https ca-certificates
sudo apt-key adv --keyserver hkp://p80.pool.sks-keyservers.net:80 --recv-keys 58118E89F3A912897C070ADBF76221572C52609D
echo "deb https://apt.dockerproject.org/repo ubuntu-trusty main" | sudo tee /etc/apt/sources.list.d/docker.list 
sudo apt update
sudo apt install -y docker-engine
sudo usermod -aG docker ubuntu
```

Then make the same edit we did on the hub, edit `/etc/init/docker.conf` and replace `DOCKER_OPTS=` in the `start` section with:

    DOCKER_OPTS="-H tcp://0.0.0.0:2375 -H unix:///var/run/docker.sock"

Restart Docker with:

    sudo service docker restart
    
Then run the container that interfaces with Swarm:

    HUB_LOCAL_IP=10.XX.XX.XX
    NODE_LOCAL_IP=$(ip route get 8.8.8.8 | awk 'NR==1 {print $NF}')
    docker run --restart=always -d swarm join --advertise=$NODE_LOCAL_IP:2375 consul://$HUB_LOCAL_IP:8500    
    
Copy the address of the Jupyterhub server in the `HUB_LOCAL_IP` variable.
    
### Setup mounting the home filesystem

    sudo apt-get install autofs

add in `/etc/auto.master`:

    /home         /etc/auto.home

create `/etc/auto.home`:

    echo "* $HUB_LOCAL_IP:/home/&" | sudo tee /etc/auto.home

using the internal IP of the hub.

    sudo service autofs restart

verify by doing:

    ls /home/ubuntu

or 

    ls /home/training01
    
you should see the same files that were on the Jupyterhub server.
    
 ### Create the same users
 
 As we are using system users and mounting the home filesystem it is important that users have the same UID on all nodes, so we are going to run
 on the node the same script we ran on the Jupyterhub server:
 
     bash create_users.sh
     
 ### Test Jupyterhub
 
 Login on the Jupyterhub instance with 2 or more different users, then check on the console of the Hub that the containers were launched on the `swarmnode` instance:
 
     docker -H :4000 ps -a
     
 ## Create more nodes
 
 Now that we created a fully functioning node we can clone it to create more to accomodate more users.
 
 ### Create a snapshot of the node
 
 First we need to delete all Docker containers, ssh into the `swarmnode` and execute:
 
     docker rm -f $(docker ps -a -q)

 Then from Compute->Instances choose "Create Snapshot", call it `swarmnodeimage`.
 
 ### Launch other nodes
 
 Click on Launch instance->"Boot from Snapshot"->`swarmnodeimage`, choose the `swarmnodesecgroup` Security Group.
 
 The 

```
#!/bin/bash
HUB_LOCAL_IP=10.XX.XX.XX
NODE_LOCAL_IP=$(ip route get 8.8.8.8 | awk 'NR==1 {print $NF}')
docker run --restart=always -d swarm join --advertise=$NODE_LOCAL_IP:2375 consul://$HUB_LOCAL_IP:8500
```

See for example Jupyterhub with 2 remote Swarm nodes running containers for 3 training users:
```
ubuntu@jupswarm:~$ docker -H :4000 ps -a                                                                 
CONTAINER ID        IMAGE                                     COMMAND                  CREATED              STATUS              PORTS                         NAMES  
204d8e5fec72        zonca/jupyterhub-datascience-systemuser   "tini -- sh /srv/sing"   27 seconds ago       Up 22 seconds       10.128.1.15:32779->8888/tcp   swarmnode/jupyter-training02  
ae099b6dad55        zonca/jupyterhub-datascience-systemuser   "tini -- sh /srv/sing"   About a minute ago   Up 55 seconds       10.128.1.15:32778->8888/tcp   swarmnode/jupyter-training01  
bcfe82dd10af        zonca/jupyterhub-datascience-systemuser   "tini -- sh /srv/sing"   21 minutes ago       Up About a minute   10.128.1.18:32768->8888/tcp   swarmnode3/jupyter-training05  
2f6b9e2d46e6        swarm                                     "/swarm join --advert"   22 minutes ago       Up 22 minutes       2375/tcp                      swarmnode3/prickly_boyd  
07cff46c6b6d        swarm                                     "/swarm join --advert"   6 hours ago          Up 4 hours          2375/tcp                      swarmnode/reverent_goldberg  
```
