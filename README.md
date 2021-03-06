# coreemu-individual-networking-labs

This repository provides tools to teachers to set up individual networking labs for students out of a blueprint. The labs are managed by the [CORE](https://github.com/coreemu/core) network emulator. 

WARNING: This software is highly experimental and should only be run on a machine in which it is an acceptable risk that users become root. It is recommended to use it only on a virtual machine that has no outbound connectivity and that only contains the labs. It must therefore also be acceptable that a user which becomes root accesses the sources of the labs. As of now, we are not aware of a way a user may become root on the host machine if he is only given access to a lab in which he accesses containers but the system is not audited and there may be fundamental exploits, or insecure labs that allow users to become root on the host. 

# Quick usage example

Follow the installation instructions. Call `sudo core-python` on the repository home directory and write:

```
>>> import handle_sessions
>>> import crypt
>>> myethernetif="enp0s3" # Replace with a wired (or dummy) interface name in your computer
>>> mypassword_to_access_a_lab="supersecret"
>>> for instance_number in range(20):
...     handle_sessions.start_unique_session("core-xmls/sniffing_lab.xml", "username_ignored_here", crypt.crypt(mypassword_to_access_a_lab), instance_number)
```

This will create 20 networking sniffing networking labs with an attacker machine on each. The users can access the attacker machines with `ssh root@10.XX.1.21` with XX = (100 + their instance number). The password is set to "supersecret" for all of them, but the loop can be modified so that each user has a different password (note that passwords encrypted with `crypt`, e.g. from a shadow file, can also be directly provided). The lab can be modified so that instead of accessing as root the string "username_ignored_here" (modified approriately) can define the user with which they connect to the attacker machine.

To kill all the labs just exit the `core-python` interpreter and run `sudo ./handle_sessions --kill -1`. You can also list existing labs with `sudo ./handle_sessions --list-sessions` and see other usages of `handle_sessions` as a script with `sudo ./handle_sessions --help`.

Next section describes how to create other lab templates and the final section of this README gives installation instructions.

# Creating labs

## Provided labs
The labs can be opened within the GUI, which is started with `sudo core-pygui`. This gives easy access to the topology and node configuration. Refer to CORE documentation for how to use the GUI.
  * `insecure_minimal_test.xml` is an insecure lab in which users will immediately gain root access to the host. It shows what should not be given to users that we want to restrict from obtaining root access to the host (give them access to a CORE node that is not a container). It also gives a simple lab that does not need docker to use the script of our repository.
  *  `sniffing_lab.xml` is a lab that gives access to an attacker machine, a docker container, that must sniff a communication between an FTP client and server. The client and server are not containers but the user cannot access them, he can only sniff their communications to obtain a flag that proves he has solved the challenge. Appropriate tools (tshar, termshark, tcpflow) are provided for the attack to be easy.
 
## Build new labs.

Under construction. Note that modifying `sniffing_lab.xml` by replacing the hub, client, and server nodes should give an easy way to obtain new labs. Modifying the attacker, firewall of rj45 nodes is not recommended without further instructions.


# Installation

## CORE installation

First of all clone [CORE](https://github.com/coreemu/core) but do not follow yet the instructions given in their documentation. Inside the CORE directory created access file `daemon/core/nodes/docker.py` and replace in the `create_container` function `--privileged` with `--cap-add=NET_ADMIN --cap-add=NET_RAW`. Doing so ensures that a user inside a docker container, even being root, has no known way to access the host machine from the container. After modifying this file follow the rest of the CORE installation instructions.

When installation is complete launch CORE with `sudo systemctl core-daemon start`. If you want it to start each time the machine boots you can enable it with `sudo systemctl enable core-daemon.service`.

## Docker installation

You can use these tools without docker, but then the users will immediately access to the host as root and must be trusted enough for that. If users are not supposed to become root (although there is some risk of it being feasible as warned above) then after installing CORE install [docker](https://www.docker.com/) following the usual installation instructions.

When installation is complete start docker with `sudo systemctl docker start`. If you want it to start it on boot you can enable it with `sudo systemctl enable docker.service`.

Note that docker has internal firewalling rules that break CORE. You must therefore modify docker's configuration for CORE to work back but this isolates containers from the network making it impossible to build new docker containers. We will therefore modify docker's configuration after next step.


## Containers installation

Clone [this repository](https://github.com/carlosaguilarmelchor/coreemu-docker-images) which contains a set of docker images for CORE and a script to build them all. Run the script to build the images. Build any other images you want to use for your labs but note that as stated in [here](https://github.com/carlosaguilarmelchor/coreemu-docker-images) some packages are mandatory for a container to work in CORE.

## Modifying docker configuration

Now follow [these instructions](https://github.com/coreemu/core/tree/master/daemon/examples/docker) to alter Docker's configuration and reboot to be able to use CORE again (believe it or not it is not enough to restart the docker service we do not know how to apply these configuration changes without rebooting the machine). If you need to use docker normally (to build new containers or for another usage of docker) you must move the `daemon.json` file you created following the instructions out of `/etc/docker` and reboot to restore normal docker functionality (and break CORE until you restore `daemon.json` and reboot again).

## Install script dependencies

The script that launches the different instances of the lab has some dependencies that need to be installed to `core-python` so run `core-python -m pip install passlib pyroute2`.

## Install lab dependencies

  * The provided `minimal_test.xml` lab requires `dropbear` lightweight SSH server on the host machine. Install it with `sudo apt install dropbear`.
  * The provided `sniffing_lab.xml` lab requires `vsftpd` FTP server on the host machine. Install it with `sudo apt install vsftpd`.

If preferred is possible to remove these dependencies on the host machine by replacing in these labs the lightweight nodes by containers in which vsftpd and dropbear are installed.




