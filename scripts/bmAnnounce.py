#!/usr/bin/env python
import argparse, yaml, xmlrpclib

parser = argparse.ArgumentParser(description="")
parser.add_argument('-r', '--repo', dest='repo', required=False)
parser.add_argument('-n', '--name', dest='name', required=False)
parser.add_argument('-d', '--desc', dest='desc', required=False)
parser.add_argument('-a', '--addr', dest='addr', required=False)
parser.add_argument('-c', '--chan', dest='chan', required=False)

args = parser.parse_args()

config = args.repo if args.repo else "../meridion-dev.yaml"
with open(config) as f:
    config = yaml.load(f.read())

guildName = args.name if args.name else config['application']['publicGuildName']
guildDescription = args.desc if args.desc else config['application']['publicGuildDescription']
bmAddress = args.addr if args.addr else config['bitmessage']['bmAddress']
bmAnnounceChannel = args.chan if args.chan else config['bitmessage']['bmAnnounce']
bmServer = config['bitmessage']['bmServer']
bmPort = config['bitmessage']['bmPort']
bmPath = config['bitmessage']['bmPath']
bmUID = config['bitmessage']['bmUser']
bmPWD = config['bitmessage']['bmPassword']

messageSubject = 'Announce: ' + guildName
messageContent = {'guildName': guildName,
                  'guildAddress': bmAddress,
                  'guildDesctiption': guildDescription}

api = xmlrpclib.ServerProxy("http://" + bmUID + ":" + bmPWD + "@" + bmServer + ":" + `bmPort` + bmPath)

ackData = api.sendMessage(bmAnnounceChannel, bmAddress, messageSubject.encode('base64'), str(messageContent).encode('base64'))

print 'Message ackData: ', ackData
