#!/usr/bin/env python

from xidb import *

def initMetadata(config):
    project = Project(config)
    project.update()

    print len(project.snapshots), "snapshots"
    print project.snapshotsLoaded, "snapshots loaded"
    print project.snapshotsCreated, "snapshots created"
    print project.assetsCreated, "metadata created"

if __name__ == "__main__": 
    parser = argparse.ArgumentParser(description="Initialize xidb metadata")
    parser.add_argument('-c', '--config', dest='config', required=True)
    args = parser.parse_args()
    print args

    with open(args.config) as f:
        config = yaml.load(f.read())
    initMetadata(config)
    
