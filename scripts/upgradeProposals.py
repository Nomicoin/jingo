#!/usr/bin/env python

import argparse, yaml, re
from xidb import Guild

parser = argparse.ArgumentParser(description="List agents in a specified guild")
parser.add_argument('-c', '--config', dest='config')
args = parser.parse_args()

conffile = args.config or "../meridion.yaml"

with open(conffile) as f:
    config = yaml.load(f.read())

guild = Guild(config)
guild.update()

for asset in guild.assets:
    if re.search("^Proposal-\d{4}\.md$", asset):
        print asset
        oldProposal = guild.assets[asset]
        print oldProposal.xid





