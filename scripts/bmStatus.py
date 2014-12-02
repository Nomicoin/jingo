#!/usr/bin/env python
# Display status of bitmessage engine 
import sys, argparse, yaml, xmlrpclib, json, time

parser = argparse.ArgumentParser(description="")
parser.add_argument('-r', '--repo', dest='repo', required=False)
parser.add_argument('-a', '--ack', dest='ackData', required=True)

args = parser.parse_args()

config = args.repo if args.repo else "../meridion-dev.yaml"
ackData = args.ackData 

with open(config) as f:
        config = yaml.load(f.read())

        serv = config['bitmessage']['bmServer']
        port = config['bitmessage']['bmPort']
        path = config['bitmessage']['bmPath']
        uid = config['bitmessage']['bmUser']
        pwd = config['bitmessage']['bmPassword']

api = xmlrpclib.ServerProxy("http://" + uid + ":" + pwd + "@" + serv + ":" + `port` + path)

while True:
    time.sleep(2)
    print 'Current status:', api.getStatus(ackData)


