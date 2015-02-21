#!/usr/bin/env python

import sys, argparse, yaml, json
from xidb import Guild

parser = argparse.ArgumentParser(description="Save a new version of an asset")
parser.add_argument('-r', '--repo', dest='repo', required=False)
parser.add_argument('-a', '--agent', dest='agent', required=True)
parser.add_argument('-x', '--xlink', dest='xlink', required=True)

args = parser.parse_args()
data = json.loads(sys.stdin.read())
title = data['pageTitle']
content = data['content']
message = data['message']

print "agent:", args.agent
print "xlink:", args.xlink
print "tile:", title
print "page:"
print "--------"
print content
print "--------"
print "message:", message

config = args.repo if args.repo else "../meridion.yaml"

with open(config) as f:
    config = yaml.load(f.read())

guild = Guild(config)
print "guild:", guild.guildProject.xid
print guild.savePage(args.agent, args.xlink, title, content, message)

