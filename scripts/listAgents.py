#!/usr/bin/env python

import argparse, yaml
from xidb import Guild

parser = argparse.ArgumentParser(description="List agents in a specified guild")
parser.add_argument('-c', '--config', dest='config', required=True)
args = parser.parse_args()

with open(args.config) as f:
    config = yaml.load(f.read())

guild = Guild(config)

for handle in guild.agents:
    agent = guild.agents[handle]
    print handle, agent.getName(), agent.getEmail()


