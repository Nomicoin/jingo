#!/usr/bin/env python

import argparse
from xidb import *

def initMetadata(config, init):
    project = Project(config)

    if init:
        project.init()
    else:
        project.update()

    print len(project.snapshots), "snapshots"
    print project.snapshotsLoaded, "snapshots loaded"
    print project.snapshotsCreated, "snapshots created"
    print project.assetsCreated, "metadata created"

if __name__ == "__main__": 
    parser = argparse.ArgumentParser(description="Initialize xidb metadata")
    parser.add_argument('-c', '--config', dest='config', required=True)
    parser.add_argument('-i', '--init', dest='init', required=False, action='store_true')
    args = parser.parse_args()
    print args

    with open(args.config) as f:
        config = yaml.load(f.read())
    initMetadata(config, args.init)
    
