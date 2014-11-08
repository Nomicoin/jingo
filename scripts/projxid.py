#!/usr/bin/env python

import argparse, yaml
from xidb import Guild

parser = argparse.ArgumentParser(description="Generate project xid")
parser.add_argument('-c', '--config', dest='config', required=True)
args = parser.parse_args()

with open(args.config) as f:
    config = yaml.load(f.read())

guild = Guild(config)
print "guild project", guild.guildProject.xid
print "repo project", guild.repoProject.xid


