#!/usr/local/bin/core-python

from core.api.grpc.client import CoreGrpcClient
from core.api.grpc.core_pb2 import (SessionState)
import grpc
from google.protobuf.json_format import MessageToJson
from functools import wraps
import argparse
import pyroute2
import os
import logging as log

ethernetif="enp0s3"

# Wrapper for functions that need access to the CORE server
def coreclient(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        core = CoreGrpcClient()
        try:
            with core.context_connect():
                return func(core, *args, **kwargs)
        except grpc.RpcError as e:
            log.error(f"grpc error: {e.details()}")

    return wrapper

# Utility functions

def info_json(message):
    json = MessageToJson(message, preserving_proto_field_name=True)
    log.info(json)

def return_json(message):
    return MessageToJson(message, preserving_proto_field_name=True)


# VLAN creation/destruction functions

def add_vlan(number):
    ipr = pyroute2.IPRoute()
    ipr.link("add", ifname=f"hsvlan_{number}", kind='vlan', link=ipr.link_lookup(ifname=ethernetif)[0],vlan_id=(100+int(number)))

def del_vlan(number):
    ipr = pyroute2.IPRoute()
    ipr.link("del", ifname=f"hsvlan_{number}")

# CLI functions

@coreclient
def start_session(core, s, stress_test):
    if stress_test:
        for i in range(stress_test):
            return_value  = core.open_xml(s, True)
            info_json(return_value)
    else:
        return_value = core.open_xml(s, True)
        info_json(return_value)
    return return_value.session_id

@coreclient
def kill_session(core, id):
    return_value = core.delete_session(id)
    info_json(return_value)

@coreclient
def kill_all_sessions(core):
    sessions = core.get_sessions().sessions
    for session in sessions:
        response = kill_session(session.id)

@coreclient
def list_sessions(core):
    return return_json(core.get_sessions())


# Most important function in the module, provides a way to:
#   * create a unique copy of a scenario file
#   * launch the scenario
#   * create appropriate vlan interfaces to give access to that instance

@coreclient
def start_unique_session(core, s, username, userpassword, usernumber):
    log.info(f"Creating unique session {usernumber} for file {s}")
    try:
        del_vlan(usernumber)
    except:
        log.info("VLAN did not exist")
    try:
        add_vlan(usernumber)
    except:
        log.error("Could not create VLAN")
        raise
    try:
        with open(s,"r") as f:
            fdata = f.read()
        fdata = fdata.replace("hsplaceholder_usernumber", str(usernumber))
        fdata = fdata.replace("hsplaceholder_user", username)
        fdata = fdata.replace("hsplaceholder_pwd", userpassword)
        fdata = fdata.replace("254.147", f"10.{usernumber+100}")
        with open(f"/tmp/handlesessions{usernumber}.xml", "w") as f:
            f.write(fdata)
    except:
        log.error("Could not create unique xml file from template")
        raise
    try:
        return_value  = core.open_xml(f"/tmp/handlesessions{usernumber}.xml", True)
        info_json(return_value)
        log.info("Instance created and started")
    except:
        try:
            log.error("Exception on instance creation removing stopped docker containers")
            os.system("docker rm $(docker ps -a -q)")
            return_value  = core.open_xml(f"/tmp/handlesessions{usernumber}.xml", True)
            info_json(return_value)
            log.info("Instance created and started")
        except:
            log.error("Could not create and start session")
            raise
    try:
        ndb = pyroute2.NDB()
        vlan_bridge_id = ndb.interfaces.dump().filter(ifname=f"hsvlan_{usernumber}")[0].master
        vlan_brdge_name = ndb.interfaces.dump().filter(index=vlan_bridge_id)[0].ifname
        ipr = pyroute2.IPRoute()
        ipr.addr('add', index=vlan_bridge_id, address=f'10.{usernumber+100}.0.2', prefixlen=24)
        ipr.route('add', dst=f"10.{usernumber+100}.0.0/16", gateway=f"10.{usernumber+100}.0.1")
        print(f"Instance is ready, access it creating a tunnel:")
        print(f"ssh -i ~/.ssh/id_rsa_tunnelctf -l tunneluser -N -L 4001:10.{usernumber+100}.1.21:22 the_ip_of_the_network_challenge_server")
        print(f"And connecting through the tunnel with: ssh -p 4001 root@127.0.0.1 using your CTFd password to authenticate")
    except:
        log.error("Could not set up bridge address and route")
        raise
    return return_value.session_id

# Main function for usage as a simple command-line tools to start/stop/list sessions.
# core-cli provides some of these functions and much more but this main gives access to functions each user can adapt
# For example this script provides a simple "kill all sessions" option and a "stress with multiple starts" option
def main():
    log.basicConfig(format='%(levelname)s:%(message)s', level=log.INFO)
    parser = argparse.ArgumentParser(description='launch or kill a coreemu session')
    parser.add_argument('-s','--start', type = str, metavar='xml_file', help='start session using xml_file as model')
    parser.add_argument('--stress-test', type = int, metavar='amount', help='start amount sessions instead of onel')
    parser.add_argument('-k','--kill', type = int, metavar='session_id', help='kill session session_id (all sessions if session_id == -1)')
    parser.add_argument('-l','--list-sessions', action="store_true", help='list existing sessions')
    args = parser.parse_args()
    if args.start:
        start_session(args.start, args.stress_test)
    elif args.kill:
        if args.kill == -1:
            kill_all_sessions()
        else:
            kill_session(args.kill)
    elif args.list_sessions:
            print(list_sessions())
    else:
        print("-s, -k or -l required")
        parser.print_help()



if __name__ == "__main__":
    main()

