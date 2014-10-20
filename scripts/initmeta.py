#!/usr/bin/env python

import argparse, shutil
from xidb import *

def initMetadata(config, args):
    project = Project(config)

    if args.rebuild:
        shutil.rmtree(project.metaDir)

    if args.init:
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
    parser.add_argument('-r', '--rebuild', dest='rebuild', required=False, action='store_true')
    args = parser.parse_args()
    print args

    with open(args.config) as f:
        config = yaml.load(f.read())
    initMetadata(config, args)
    
