#!/usr/bin/env python

import argparse, yaml, re
from xidb import Guild
from xidb.utils import *

class Proposal:
    def __init__(self, xid, cid, sha, name):
        self.xid = xid
        self.cid = cid
        self.sha = sha
        self.name = name
        self.propid = name[9:13]
        self.props = dict()
        self.source = createLink(xid, cid)
        self.xlink = self.source #needed in guild.commitFile
        self.title = ''
        self.type = ''
        self.status = ''
        self.sponsors = []
        self.rationale = ''

    def getName(self):
        return self.propid + ".json"

    def init(self, blob):
        self.text = blob.data.decode('utf-8')
        self.parse()
        self.resolve()

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
                if line[0:2] == "* ":
                    line = line[2:] # remove wiki bullets
                print key, line
                self.props[key].append(line)

    def resolve(self):
        if 'title' in self.props:
            self.title = self.props['title'][0]

        if 'sponsor' in self.props:
            self.sponsors = self.props['sponsor']

        if 'status' in self.props:
            self.status = self.props['status'][0]

        if 'type' in self.props:
            self.type = self.props['type'][0]

        if 'rationale' in self.props:
            self.rationale = "\n".join(self.props['rationale'])

        self.data = dict(title=self.title,
                         propid=self.propid,
                         source=self.source,
                         status=self.status,
                         type=self.type,
                         sponsors=self.sponsors,
                         rationale=self.rationale)

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
        print guild.saveProposal("macterra", prop)
