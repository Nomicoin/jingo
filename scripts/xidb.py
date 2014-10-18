import uuid, os, shutil, yaml, json, mimetypes
from pygit2 import *
from datetime import datetime
from genxid import genxid

def createLink(xid, hash):
    xidRef = str(xid)[:8]
    hashRef = str(hash)[:8]
    return os.path.join(xidRef, hashRef)

def saveFile(path, obj):
    with open(path, 'w') as f:
        res = json.dumps(obj, sort_keys=True, indent=4, separators=(',', ': '))
        f.write(res + "\n")

class Asset:
    def __init__(self, id, xid, name):
        self.xid = str(xid)
        self.name = name
        self.versions = [str(id)]

        ext = os.path.splitext(name)[1]
        if ext in mimetypes.types_map:
            self.type = mimetypes.types_map[ext]
        else:
            self.type = ''

    def addVersion(self, id):
        latest = self.versions[-1]
        if (id != latest):
            self.versions.append(str(id))

    def prevLink(self, id):
        i = self.versions.index(id)
        if i > 0:
            prev = self.versions[i-1]
            return createLink(self.xid, prev)
        else:
            return ''

class Snapshot:
    def __init__(self, commit, link, path):
        self.commit = commit
        self.link = link
        self.path = path
        self.timestamp = datetime.fromtimestamp(commit.commit_time).isoformat()
        self.assets = {}

    def add(self, id, asset):
        self.assets[str(id)] = {'xid': asset.xid, 'name': asset.name}

    def __str__(self):
        return "snapshot %s at %s" % (self.link, self.timestamp)

class Project:
    def __init__(self, config):
        self.repoDir = config['application']['repository']
        self.metaDir = config['application']['metadata']
        self.repo = Repository(self.repoDir)
        self.xid = self.genxid()
        self.snapshots = []
        self.assets = {}
        self.snapshotsLoaded = 0
        self.snapshotsCreated = 0
        self.assetsLoaded = 0
        self.assetsCreated = 0
        self.saveIndex() # until javascript can generate xid

    def genxid(self):
        walker = self.repo.walk(self.repo.head.target, GIT_SORT_TIME | GIT_SORT_REVERSE)
        commit = walker.next()
        xid = genxid(commit.id, commit.tree.id)
        return str(xid)

    def init(self): 
        self.initSnapshots()
        self.initMetadata(True)

    def update(self):
        self.updateSnapshots()
        self.initMetadata()

    def saveIndex(self):
        if not os.path.exists(self.metaDir):
            os.makedirs(self.metaDir)

        path = os.path.join(self.metaDir, "index.json")
        if os.path.exists(path):
            with open(path) as f:
                try:
                    projects = json.loads(f.read())['projects']
                except:
                    projects = {}
        else:
            projects = {}

        projects[self.repo.path] = self.xid
        saveFile(path, {'projects': projects})

    def createPath(self, link):
        path = os.path.join(self.metaDir, link) + ".json"
        dirName = os.path.dirname(path)
        if not os.path.exists(dirName):
            os.makedirs(dirName)
        return path

    def addTree(self, tree, path, snapshot):
        # todo: don't add metadir to assets
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
                    xid = genxid(snapshot.commit.id, obj.id)
                    asset = Asset(obj.id, xid, name)
                    self.assets[name] = asset
                snapshot.add(obj.id, asset)
        
    def updateSnapshots(self):
        for commit in self.repo.walk(self.repo.head.target, GIT_SORT_TIME):
            link = createLink(self.xid, commit.id)
            path = self.createPath(link)
            snapshot = Snapshot(commit, link, path)
            self.snapshots.insert(0, snapshot)
            if os.path.exists(path):
                break
        self.loadSnapshots()

    def initSnapshots(self):
        for commit in self.repo.walk(self.repo.head.target, GIT_SORT_TIME | GIT_SORT_REVERSE):
            link = createLink(self.xid, commit.id)
            path = self.createPath(link)
            snapshot = Snapshot(commit, link, path)
            self.snapshots.append(snapshot)
        self.loadSnapshots()

    def loadSnapshots(self):
        for snapshot in self.snapshots:
            if os.path.exists(snapshot.path):
                print "Loading snapshot", snapshot.path
                with open(snapshot.path) as f:
                    assets = json.loads(f.read())['assets']
                for id in assets:
                    asset = assets[id]
                    xid = asset['xid']
                    name = asset['name']
                    if name in self.assets:
                        asset = self.assets[name]
                        asset.addVersion(id)
                    else:
                        #print "Adding %s as %s" % (name, xid)
                        asset = Asset(id, xid, name)
                        self.assets[name] = asset
                    snapshot.add(id, asset)
                self.snapshotsLoaded += 1
            else:
                print "Building snapshot", snapshot.link
                self.addTree(snapshot.commit.tree, '', snapshot)

                metaCommit = {
                    'project': str(self.xid),
                    'author': snapshot.commit.author.name,
                    'email': snapshot.commit.author.email,
                    'time': snapshot.timestamp,
                    'message': snapshot.commit.message,
                    'commit': str(snapshot.commit.id)
                }

                saveFile(snapshot.path, {'xidb': metaCommit, 'assets': snapshot.assets})
                self.snapshotsCreated += 1

    def initMetadata(self, rewrite=False):
        for snapshot in self.snapshots:
            for hash in snapshot.assets:
                try:
                    blob = self.repo[hash]
                except:
                    print "bad blob?", snapshot.assets[hash]
                    continue

                if blob.type != GIT_OBJ_BLOB:
                    continue
                
                asset = snapshot.assets[hash]
                xid = asset['xid']
                name = asset['name']
                link = createLink(xid, hash)
                path = self.createPath(link)
                asset = self.assets[name]
                if rewrite or not os.path.isfile(path):
                    prevLink = asset.prevLink(hash)
                    meta = {
                        'xid': str(xid),
                        'snapshot': snapshot.link,
                        'prev': prevLink,
                        'next': '',
                        'type': asset.type,
                        'link': link,
                        'name': name,
                        'description': '',
                        'authors': str([]),
                        'timestamp': snapshot.timestamp,
                        'asset': hash, 
                        'size': blob.size,
                        'encoding': 'binary' if blob.is_binary else 'text',
                        'comments': '',
                        'votes': ''
                    }
                    saveFile(path, {'xidb': meta})
                    print "wrote metadata for", name, link
                    self.assetsCreated += 1

                    prevPath = self.createPath(prevLink)
                    if os.path.isfile(prevPath):
                        with open(prevPath) as f:
                            meta = json.loads(f.read())['xidb']
                        meta['next'] = link
                        saveFile(prevPath, {'xidb': meta})
