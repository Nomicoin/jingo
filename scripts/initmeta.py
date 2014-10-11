import uuid, toml, os, shutil
from pygit2 import *
from datetime import datetime

class File:
    def __init__(self, entry):
        self.xid = uuid.uuid4()
        self.entry = entry

class Snapshot:
    def __init__(self, commit):
        self.commit = commit
        self.xids = {}

    def add(self, entry, xid):
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
    pathId = os.path.join(xidRef, hashRef)
    dirName = os.path.join(".meta", xidRef)
    metadata = hashRef + ".toml"
    path = os.path.join(dirName, metadata)
    if not os.path.exists(dirName):
        os.makedirs(dirName)
    return path, pathId

project = Project()
project.init('/home/david/dev/Meridion.wiki/.git')

print len(project.snapshots)

if os.path.exists('.meta'):
    shutil.rmtree('.meta')

for snapshot in project.snapshots:
    path, commitLink  = createPath(project.xid, snapshot.commit.id)
    dt = datetime.fromtimestamp(snapshot.commit.commit_time)
    metaCommit = {
        'project': str(project.xid),
        'author': snapshot.commit.author.name,
        'email': snapshot.commit.author.email,
        'time': dt.isoformat(),
        'message': snapshot.commit.message,
        'commit': str(snapshot.commit.id)
    }

    with open(path, 'w') as f:
        f.write(toml.dumps({'commit': metaCommit, 'assets': snapshot.xids}))

    for hash in snapshot.xids:
        blob = project.repo[hash]
        if blob.type != GIT_OBJ_BLOB:
            continue
        xid, name = snapshot.xids[hash]
        path, blobLink = createPath(xid, hash)
        if not os.path.isfile(path):
            meta = {
                'xid': str(xid),
                'commit': commitLink,
                'type': '',
                'link': blobLink,
                'name': name,
                'description': '',
                'authors': str([]),
                'timestamp': dt.isoformat(),
                'asset': hash, 
                'size': blob.size,
                'encoding': 'binary' if blob.is_binary else 'text',
                'comments': '',
                'votes': ''
            }
            print meta
            with open(path, 'w') as f:
                f.write(toml.dumps({'xidb': meta}))

save = { 'project': { 'repo': project.repo.path, 'xid': str(project.xid) } }

with open(os.path.join(".meta", "index.toml"), 'w') as f:
    f.write(toml.dumps(save))
