#!/usr/bin/env python

import sys, argparse, yaml
from xidb import Guild

parser = argparse.ArgumentParser(description="Save a new version of an asset")
parser.add_argument('-r', '--repo', dest='repo', required=False)
parser.add_argument('-a', '--agent', dest='agent', required=True)
parser.add_argument('-t', '--title', dest='title', required=True)

args = parser.parse_args()
asset = sys.stdin.read()

print "agent:", args.agent
print "title:", args.title

config = args.repo if args.repo else "../meridion.yaml"

with open(config) as f:
    config = yaml.load(f.read())

guild = Guild(config)
print "guild:", guild.guildProject.xid
print guild.newStrain(args.agent, args.title)
