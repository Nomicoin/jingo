import uuid, toml, os, shutil
from pygit2 import *
from datetime import datetime

class Asset:
    def __init__(self, id, xid, name):
        self.xid = str(xid)
        self.name = name
        self.versions = [str(id)]

    def addVersion(self, id):
        latest = self.versions[-1]
        if (id != latest):
            self.versions.append(str(id))

    def prevLink(self, id):
        i = self.versions.index(id)
        if i > 0:
            prev = self.versions[i-1]
            return createPath(self.xid, prev)[1]
        else:
            return ''

class Snapshot:
    def __init__(self, commit):
        self.commit = commit
        self.xids = {}

    def add(self, id, asset):
        self.xids[str(id)] = [asset.xid, asset.name]

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
                    self.xid = str(uuid.uuid4())
                    projects[self.repo.path] = self.xid
                    self.save(projects)
        else:
            self.xid = str(uuid.uuid4())
            self.save({ self.repo.path: self.xid })

    def save(self, projects):
            metaDir = os.path.dirname(self.path)
            if not os.path.exists(metaDir):
                os.makedirs(metaDir)
            with open(self.path, 'w') as f:
                f.write(toml.dumps({'projects': projects}))

    def init(self):
        self.initSnapshots()
        self.initMetadata()

    def addTree(self, tree, path, snapshot):
        for entry in tree:
            try:
                obj = self.repo[entry.id]
            except:
                print "bad id?", entry.id
                continue
            if obj.type == GIT_OBJ_TREE:
                self.addTree(obj, os.path.join(path, entry.name), snapshot)
            elif obj.type == GIT_OBJ_BLOB:
                name = os.path.join(path, entry.name)
                if name in self.assets:
                    asset = self.assets[name]
                    asset.addVersion(obj.id)
                else:
                    asset = Asset(obj.id, uuid.uuid4(), name)
                    self.assets[name] = asset
                snapshot.add(obj.id, asset)
        
    def initSnapshots(self):
        for commit in self.repo.walk(self.repo.head.target, GIT_SORT_TIME | GIT_SORT_REVERSE):
            snapshot = Snapshot(commit)
            path, link = createPath(self.xid, commit.id)
            print "Building snapshot", link
            if os.path.exists(path):
                with open(path) as f:
                    assets = toml.loads(f.read())['assets']
                for id in assets:
                    xid, name = assets[id]
                    if name in self.assets:
                        asset = self.assets[name]
                        asset.addVersion(id)
                    else:
                        print "Adding %s as %s" % (name, xid)
                        asset = Asset(id, xid, name)
                        self.assets[name] = asset
                    snapshot.add(id, asset)
            else:
                self.addTree(commit.tree, '', snapshot)

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
                try:
                    blob = self.repo[hash]
                except:
                    print "bad blob?", snapshot.xids[hash]
                    continue

                if blob.type != GIT_OBJ_BLOB:
                    continue
                xid, name = snapshot.xids[hash]
                path, blobLink = createPath(xid, hash)
                asset = self.assets[name]
                if os.path.isfile(path):
                    print "found metadata for", name, blobLink
                else:
                    meta = {
                        'xid': str(xid),
                        'commit': commitLink,
                        'prev': asset.prevLink(hash),
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
                        print "wrote metadata for", name, blobLink

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
#project = Project('/home/david/dev/jingo/.git')
#project = Project('/home/david/dev/test/.git')
project.open()
project.init()

print len(project.snapshots)



