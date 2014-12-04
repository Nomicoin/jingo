#!/usr/bin/env python
#
# This script processes incoming events from bitmessages
#
# Supported cases:
#  1) Messages received on Announce address 
#  2) Respond to requests for public repositories
#  3) Handle foreign guild repository list
#  4) Respond to requests to subscribe to a repository
#

import argparse, yaml, xmlrpclib, json

parser = argparse.ArgumentParser(description='')
parser.add_argument('-r', '--repo', dest='repo', required=False)

args = parser.parse_args()

config = args.repo if args.repo else '../meridion-dev.yaml'
with open(config) as f:
    config = yaml.load(f.read())

guildDir = config['application']['guild']
guildName = config['application']['publicGuildName']
guildDesc = config['application']['publicGuildDescription']
bmServer = config['bitmessage']['bmServer']
bmPort = config['bitmessage']['bmPort']
bmPath = config['bitmessage']['bmPath']
bmUID = config['bitmessage']['bmUser']
bmPWD = config['bitmessage']['bmPassword']
bmAddress = config['bitmessage']['bmAddress']
bmAnnounceChannel = config['bitmessage']['bmAnnounce']

# Received announce message on global announce channel
def announce():
    print 'announcement from ' + inboxMessage['fromAddress']
    try:
        announceInfo = yaml.load(inboxMessage['message'].decode('base64'))
    except yaml.YAMLError, exc:
        print 'Received invalid YAML announce data: ', exc
    else:
        with open(guildDir + '/announce/' + inboxMessage['fromAddress'] + '.yaml','w') as announceFile:
            yaml.dump(announceInfo, announceFile)

# Request for published repositories
def getRepos():
    print 'request for published repos from ' + inboxMessage['fromAddress']
    with open(guildDir + '/pubrepo.yaml') as publicRepoFile:
        pubrepo = yaml.load(publicRepoFile.read())
    ackData = api.sendMessage(inboxMessage['fromAddress'], bmAddress, 'Repo List'.encode('base64'), yaml.dump(pubrepo).encode('base64'))
    print 'sent public repositories. ' + ackData

# Process remote repository list
def repoList():
    print 'received published repos list from ' + inboxMessage['fromAddress']
    try:
        repoList = yaml.load(inboxMessage['message'].decode('base64'))
    except yaml.YAMLError, exc:
        print 'Received invalid YAML repository list: ', exc
    else:
        with open(guildDir + '/announce/' + inboxMessage['fromAddress'] + '-repos.yaml','w') as repoFile:
            yaml.dump(repoList, repoFile)

# Request to subscribe to published repository
def subscribe():
    print 'request to subscribe to repo '

    with open(guildDir + '/pubrepo.yaml') as publicRepoFile:
        publicRepositories = yaml.load(publicRepoFile.read())
    
    try:
        subRequest = yaml.load(inboxMessage['message'].decode('base64'))
    except yaml.YAMLError, exc:
        print 'Received invalid subscription request: ', exc
    else:
        for publicRepo in publicRepositories['publicRepos']:
            try:
                if publicRepo['folderId'] == subRequest['folderId']:
                    requestorDeviceId = subRequest['deviceId'] 
                    print '***process syncthing registration here...'
            except: 
                print 'Received invalid subscription request.'

# Invalid request handler
def invalidRequest():
    print 'message contains an invalid request: ' + inboxMessage['subject'].decode('base64')

# Let's get connected to our bitmessage instance
api = xmlrpclib.ServerProxy('http://' + bmUID + ':' + bmPWD + '@' + bmServer + ':' + `bmPort` + bmPath)
allInboxMessages = json.loads(api.getAllInboxMessages())

for inboxMessage in allInboxMessages['inboxMessages']:
    # Message received on Announce channel
    if inboxMessage['toAddress'] == bmAnnounceChannel:
        announce()
    else:
        inboxRequest = {'Get Repos' : getRepos,
                        'Repo List' : repoList,
                        'Subscribe' : subscribe,
        }
        inboxRequest.get(inboxMessage['subject'].decode('base64'), invalidRequest)()

    print 'All is done. Delete message.' 
    print ''

