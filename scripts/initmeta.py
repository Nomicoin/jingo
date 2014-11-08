#!/usr/bin/env python

import argparse, shutil, yaml
from xidb import Guild

def initMetadata(args):
    with open(args.config) as f:
        config = yaml.load(f.read())

    guild = Guild(config)

    if args.rebuild:
        shutil.rmtree(guild.metaDir, ignore_errors=True)

    if args.init:
        guild.init()
    else:
        guild.update()

    print
    print args
    print guild.repoProject.snapshotsLoaded, "snapshots loaded"
    print guild.repoProject.snapshotsCreated, "snapshots created"
    print guild.repoProject.assetsCreated, "metadata created"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialize xidb metadata")
    parser.add_argument('-c', '--config', dest='config', required=True)
    parser.add_argument('-i', '--init', dest='init', required=False, action='store_true')
    parser.add_argument('-r', '--rebuild', dest='rebuild', required=False, action='store_true')
    initMetadata(parser.parse_args())

