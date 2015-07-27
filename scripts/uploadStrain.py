#!/usr/bin/env python

import sys, argparse, yaml
from xidb import Guild

parser = argparse.ArgumentParser(description="Save an uploaded file to a strain folder")
parser.add_argument('-r', '--repo', dest='repo', required=False)
parser.add_argument('-a', '--agent', dest='agent', required=True)
parser.add_argument('-u', '--upload', dest='upload', required=True)
parser.add_argument('-n', '--name', dest='name', required=True)
parser.add_argument('-f', '--field', dest='field', required=True)
parser.add_argument('-s', '--strain', dest='strain', required=True)

args = parser.parse_args()
asset = sys.stdin.read()

print "agent:", args.agent
print "upload:", args.upload
print "name:", args.name
print "field:", args.field
print "strain:", args.strain

config = args.repo if args.repo else "../meridion.yaml"

with open(config) as f:
    config = yaml.load(f.read())

guild = Guild(config)
print "guild:", guild.guildProject.xid
print guild.uploadStrain(args.agent, args.upload, args.name, args.field, args.strain)

