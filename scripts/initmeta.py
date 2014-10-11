import uuid, toml, os, shutil
from pygit2 import *
from datetime import datetime

class Asset:
    def __init__(self, entry, xid):
        self.xid = xid
        self.entry = entry

class Snapshot:
    def __init__(self, commit):
        self.commit = commit
        self.xids = {}

    def add(self, entry, xid):
        self.xids[entry.hex] = [str(xid), entry.name]

class Project:
    def __init__(self, repoDir):
        self.repo = Repository(repoDir)
        self.snapshots = []
        self.assets = {}
        self.path = os.path.join(".meta", "index.toml")
 
    def open(self):
        if os.path.exists(self.path):
            with open(self.path) as f:
                projects = toml.loads(f.read())['projects']
                if self.repo.path in projects:
                    self.xid = projects[self.repo.path]
                else:
                    self.save()
        else:
            self.save()

    def save(self):
            self.xid = str(uuid.uuid4())
            save = { 'projects': { self.repo.path: str(self.xid) } }
            
            metaDir = os.path.dirname(self.path)
            if not os.path.exists(metaDir):
                os.makedirs(metaDir)

            with open(self.path, 'w') as f:
                f.write(toml.dumps(save))

    def init(self):
        self.initSnapshots()
        self.initMetadata()

    def initSnapshots(self):
        for commit in self.repo.walk(self.repo.head.target, GIT_SORT_TIME | GIT_SORT_REVERSE):
            snapshot = Snapshot(commit)
            path, link = createPath(self.xid, commit.id)
            if os.path.exists(path):
                with open(path) as f:
                    assets = toml.loads(f.read())['assets']
                for id in assets:
                    xid, name = assets[id]
                    entry = commit.tree[name]
                    if name in self.assets:
                        asset = self.assets[entry.name]
                    else:
                        print "Adding %s as %s" % (name, xid)
                        self.assets[name] = Asset(entry, xid)
                    snapshot.add(entry, xid)
            else:
                for entry in commit.tree:
                    if entry.name in self.assets:
                        asset = self.assets[entry.name]
                    else:
                        asset = Asset(entry, uuid.uuid4())
                        self.assets[entry.name] = asset
                        print "Adding", entry.name
                    snapshot.add(entry, asset.xid)

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

            self.snapshots.append(snapshot)
                        
    def initMetadata(self):
        for snapshot in self.snapshots:
            path, commitLink  = createPath(self.xid, snapshot.commit.id)
            dt = datetime.fromtimestamp(snapshot.commit.commit_time)

            for hash in snapshot.xids:
                blob = self.repo[hash]
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
                    with open(path, 'w') as f:
                        f.write(toml.dumps({'xidb': meta}))
                        print "wrote metadata for", name

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

project = Project('/home/david/dev/Meridion.wiki/.git')
project.open()
project.init()

print len(project.snapshots)



