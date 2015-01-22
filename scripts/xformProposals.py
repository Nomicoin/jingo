#!/usr/bin/env python

import argparse, yaml, re
from xidb import Guild

class Proposal:
    def __init__(self, xid, cid, sha, name):
        self.xid = xid
        self.cid = cid
        self.sha = sha
        self.name = name
        self.props = dict()

    def init(self, blob):
        self.text = blob.data.decode('utf-8')
        self.parse()

    def parse(self):
        key = 'foo'
        for line in iter(self.text.splitlines()):
            line = line.strip()
            if not line:
                continue
            keyMatch = re.search("^# (.*)", line)
            if keyMatch:
                key = keyMatch.group(1)
                print 'key', key
                self.props[key] = []
            else:
                print key, line
                self.props[key].append(line)

parser = argparse.ArgumentParser(description="Upgrade markdown proposals to json")
parser.add_argument('-c', '--config', dest='config')
args = parser.parse_args()

conffile = args.config or "../meridion.yaml"

with open(conffile) as f:
    config = yaml.load(f.read())

guild = Guild(config)
guild.update()

project = guild.repoProject
snapshot = project.snapshots[-1]
print snapshot
assets = snapshot.assets

for xid in assets:
    asset = assets[xid]
    name = asset['name']
    if re.search("^Proposal-\d{4}\.md$", name):
        print asset
        cid = asset['commit']
        sha = asset['sha']
        prop = Proposal(xid, cid, sha, name)
        blob = project.repo[sha]
        prop.init(blob)
        print prop.props
