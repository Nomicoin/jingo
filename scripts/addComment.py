#!/usr/bin/env python

import sys, argparse, yaml
from xidb import Project

parser = argparse.ArgumentParser(description="Add comment to an asset")
parser.add_argument('-r', '--repo', dest='repo', required=True)
parser.add_argument('-a', '--agent', dest='agent', required=True)
parser.add_argument('-x', '--xlink', dest='xlink', required=True)
args = parser.parse_args()
lines = sys.stdin.readlines()
comment = "".join(lines)

print "repo:", args.repo
print "agent:", args.agent
print "xlink:", args.xlink
print "comment:"
print "--------"
print comment
print "--------"

if args.repo == "Meridion":
    config = "../meridion.yaml"

if args.repo == "Viki":
    config = "../viki.yaml"

with open(config) as f:
    config = yaml.load(f.read())

project = Project(config)
print project.xid

agent = project.getAgent(args.agent)
asset = project.getAsset(args.xlink)
clink = agent.addComment(asset, comment)

print clink

