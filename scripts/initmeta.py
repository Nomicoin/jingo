from pygit2 import *
import uuid, toml, os

class File:
    def __init__(self, entry):
        self.xid = uuid.uuid4()
        self.entry = entry

class Snapshot:
    def __init__(self, commit):
        self.commit = commit
        self.files = {}
        self.xids = {}

    def add(self, entry, xid):
        metadata = str(xid)[:8] + "|" + str(entry.id)[:8]
        self.files[entry.name] = metadata
        self.xids[entry.hex] = metadata

class Project:
    def __init__(self):
        self.xid = uuid.uuid4()
        self.snapshots = []
        self.files = {}
    
    def init(self, repoDir):
        self.repo = Repository(repoDir)
        for commit in self.repo.walk(self.repo.head.target, GIT_SORT_TIME | GIT_SORT_REVERSE):
            snapshot = Snapshot(commit)
            for entry in commit.tree:
                if entry.name in self.files:
                    file = self.files[entry.name]
                else:
                    file = File(entry)
                    self.files[entry.name] = file
                    print "adding", entry.name
                snapshot.add(entry, file.xid)
            self.snapshots.append(snapshot)

project = Project()
project.init('/home/david/dev/Meridion.wiki/.git')

print len(project.snapshots)

latest = project.snapshots[-1]
#print latest.files

print toml.dumps(latest.xids)

for snapshot in project.snapshots:
    metadata = str(project.xid)[:8] + "|" + str(snapshot.commit.id)[:8]
    path = os.path.join(".meta", *metadata.split("|")) + ".toml"
    print metadata, path, len(snapshot.xids)

    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))

    with open(path, 'w') as f:
        f.write(toml.dumps(snapshot.xids))








