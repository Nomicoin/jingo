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
        #metadata = str(xid)[:8] + "|" + str(entry.id)[:8]
        #self.files[entry.name] = metadata
        self.xids[entry.hex] = [str(xid), entry.name]

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

def createPath(xid, hash):
    xidRef = str(xid)[:8]
    hashRef = str(hash)[:8]
    dirName = os.path.join(".meta", xidRef)
    metadata = hashRef + ".toml"
    path = os.path.join(dirName, metadata)
    if not os.path.exists(dirName):
        os.makedirs(dirName)
    return path

project = Project()
project.init('/home/david/dev/Meridion.wiki/.git')

print len(project.snapshots)

#latest = project.snapshots[-1]
#print toml.dumps(latest.xids)

for snapshot in project.snapshots:
    path = createPath(project.xid, snapshot.commit.id)
    with open(path, 'w') as f:
        f.write(toml.dumps(snapshot.xids))
    for hash in snapshot.xids:
        xid, name = snapshot.xids[hash]
        path = createPath(xid, hash)
        print path, name

save = { 'project': { 'repo': project.repo.path, 'xid': str(project.xid) } }

with open(os.path.join(".meta", "index.toml"), 'w') as f:
    f.write(toml.dumps(save))
