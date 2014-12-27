#!/usr/bin/env python

import sys, argparse, yaml
from xidb import Guild

parser = argparse.ArgumentParser(description="Save a new version of an asset")
parser.add_argument('-r', '--repo', dest='repo', required=False)
parser.add_argument('-a', '--agent', dest='agent', required=True)
parser.add_argument('-x', '--xlink', dest='xlink', required=True)

args = parser.parse_args()
asset = sys.stdin.read()

print "agent:", args.agent
print "xlink:", args.xlink
print "asset:"
print "--------"
print asset
print "--------"

config = args.repo if args.repo else "../meridion.yaml"

with open(config) as f:
    config = yaml.load(f.read())

guild = Guild(config)
print guild.guildProject.xid
print guild.saveAsset(args.agent, args.xlink, asset)

