#!/usr/bin/env python

from xidb import *

parser = argparse.ArgumentParser(description="Generate project xid")
parser.add_argument('-c', '--config', dest='config', required=True)
args = parser.parse_args()

with open(args.config) as f:
    config = yaml.load(f.read())

project = Project(config)
print project.xid

    
