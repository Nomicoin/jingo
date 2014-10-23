import uuid, os, shutil, yaml, json, mimetypes
from pygit2 import *
from datetime import datetime
from genxid import genxid
from xitypes import *

def createLink(xid, hash):
    xidRef = str(xid)[:8]
    hashRef = str(hash)[:8]
    return os.path.join(xidRef, hashRef)

def saveFile(path, obj):
    with open(path, 'w') as f:
        res = json.dumps(obj, sort_keys=True, indent=4, separators=(',', ': '))
        f.write(res + "\n")

class Asset:
    def __init__(self, cid, oid, xid, name):
        self.xid = str(xid)
        self.name = name
        self.cid = str(cid)
        self.oid = str(oid)

        ext = os.path.splitext(name)[1]
        if ext in mimetypes.types_map:
            self.type = mimetypes.types_map[ext]
        elif ext in otherTypes:
            self.type = otherTypes[ext]
        else:
            self.type = ''

    def addVersion(self, cid, oid):
        oid = str(oid)
        cid = str(cid)
        if (self.oid != oid):
            #print "new version for", self.name, self.oid, oid
            self.oid = oid
            self.cid = cid

    def metadata(self, blob):
        data = {}
        data['xidb'] = {
            'xid': self.xid,
            'snapshot': '',
            'type': self.type,
            'name': self.name,
            'description': '',
            'authors': '',
            'asset': str(blob.id), 
            'size': blob.size,
            'encoding': 'binary' if blob.is_binary else 'text',
            'comments': '',
            'votes': ''
        }

        if self.type in typeIndex:
            typeIndex[self.type].addMetadata(self, blob, data)

        return data

class Snapshot:
    def __init__(self, commit, link, path):
        self.commit = commit
        self.link = link
        self.path = path
        self.timestamp = datetime.fromtimestamp(commit.commit_time).isoformat()
        self.assets = {}

    def add(self, asset):
        self.assets[asset.xid] = {
            'name': asset.name,
            'commit': asset.cid,
            'oid': asset.oid
        }

    def __str__(self):
        return "snapshot %s at %s" % (self.link, self.timestamp)

    def metadata(self):
        data = {}
        data['xidb'] = {
            'link': self.link,
            'author': self.commit.author.name,
            'email': self.commit.author.email,
            'timestamp': self.timestamp,
            'message': self.commit.message,
            'commit': str(self.commit.id)
        }
        data['assets'] = self.assets
        return data

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

    def genxid(self):
        walker = self.repo.walk(self.repo.head.target, GIT_SORT_TIME | GIT_SORT_REVERSE)
        commit = walker.next()
        xid = genxid(commit.id, commit.tree.id)
        return str(xid)

    def init(self): 
        self.initSnapshots()
        self.initMetadata(True)
        self.saveSnapshots()
        self.saveIndex() # until javascript can generate xid

    def update(self):
        self.updateSnapshots()
        self.initMetadata()
        self.saveSnapshots()
        self.saveIndex() # until javascript can generate xid

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
                    asset.addVersion(snapshot.commit.id, obj.id)
                else:
                    xid = genxid(snapshot.commit.id, obj.id)
                    asset = Asset(snapshot.commit.id, obj.id, xid, name)
                    self.assets[name] = asset
                snapshot.add(asset)
        
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
        self.loadSnapshots(True)

    def loadSnapshots(self, rewrite=False):
        for snapshot in self.snapshots:
            if not rewrite and os.path.exists(snapshot.path):
                print "Loading snapshot", snapshot.path
                with open(snapshot.path) as f:
                    assets = json.loads(f.read())['assets']
                for xid in assets:
                    info = assets[xid]
                    name = info['name']
                    commit = info['commit']
                    oid = info['oid']
                    if name in self.assets:
                        asset = self.assets[name]
                        asset.addVersion(snapshot.commit.id, oid)
                    else:
                        #print "Adding %s as %s" % (name, xid)
                        asset = Asset(commit, oid, xid, name)
                        self.assets[name] = asset
                    snapshot.add(asset)
                self.snapshotsLoaded += 1
            else:
                print "Building snapshot", snapshot.link
                self.addTree(snapshot.commit.tree, '', snapshot)
                metadata = snapshot.metadata()
                metadata['xidb']['project'] = self.xid
                self.snapshotsCreated += 1

    def saveSnapshots(self):
        for snapshot in self.snapshots:
            saveFile(snapshot.path, snapshot.metadata())
            print "saved snapshot", snapshot.path

    def initMetadata(self, rewrite=False):
        for snapshot in self.snapshots:
            for xid in snapshot.assets:
                info = snapshot.assets[xid]
                name = info['name']
                oid = info['oid']
                cid = info['commit']

                try:
                    blob = self.repo[oid]
                except:
                    print "bad blob?", info
                    continue

                if blob.type != GIT_OBJ_BLOB:
                    continue

                link = createLink(xid, cid)
                path = self.createPath(link)
                asset = self.assets[name]

                if not os.path.isfile(path):
                    metadata = asset.metadata(blob)
                    metadata['xidb']['link'] = link
                    metadata['xidb']['snapshot'] = snapshot.link
                    metadata['xidb']['timestamp'] = snapshot.timestamp
                        
                    saveFile(path, metadata)
                    print "wrote metadata for", link, name
                    self.assetsCreated += 1

            prevSnapshot = snapshot