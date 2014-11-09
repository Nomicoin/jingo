#!/usr/bin/env python

import argparse, yaml
from xidb import Guild

parser = argparse.ArgumentParser(description="List agents in a specified guild")
parser.add_argument('-c', '--config', dest='config', required=True)
args = parser.parse_args()

with open(args.config) as f:
    config = yaml.load(f.read())

guild = Guild(config)

for email in guild.agents:
    agent = guild.agents[email]
    print agent.xid, agent.name, agent.email


