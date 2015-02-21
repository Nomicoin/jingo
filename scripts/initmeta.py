#!/usr/bin/env python

import argparse, yaml
from xidb import Guild

def initMetadata(args):
    with open(args.config) as f:
        config = yaml.load(f.read())

    guild = Guild(config, args.rebuild)

    if args.init:
        guild.init()
    else:
        guild.update()

    print
    print args
    print guild.wikiProject.snapshotsLoaded, "snapshots loaded"
    print guild.wikiProject.snapshotsCreated, "snapshots created"
    print guild.wikiProject.assetsCreated, "metadata created"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialize xidb metadata")
    parser.add_argument('-c', '--config', dest='config', required=True)
    parser.add_argument('-i', '--init', dest='init', required=False, action='store_true')
    parser.add_argument('-r', '--rebuild', dest='rebuild', required=False, action='store_true')
    initMetadata(parser.parse_args())

