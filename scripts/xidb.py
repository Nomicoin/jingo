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

otherTypes = {
    '.md': 'text/markdown',
    '.jade': 'text/jade',
    '.toml': 'text/toml',
    '.yaml': 'text/yaml'
} 

class Text:
    def addMetadata(self, asset, blob, metadata):
        if blob.is_binary:
            lines = 0
        else:
            lines = blob.data.count('\n')

        metadata['text'] = { 'lines': lines }
        return metadata

class Markdown:
    def __init__(self):
        self.text = Text()

    def addMetadata(self, asset, blob, metadata):
        self.text.addMetadata(asset, blob, metadata)
        metadata['markdown'] = { 'asHtml5': 'xlink' }
        return metadata
        
class Image:
    def addMetadata(self, asset, blob, metadata):
        metadata['image'] = { 
            'width': 0,
            'height': 0,
            'colorDepth': 0
        }
        return metadata

class Png:
    def __init__(self):
        self.image = Image()

    def addMetadata(self, asset, blob, metadata):
        self.image.addMetadata(asset, blob, metadata)
        metadata['png'] = {}
        return metadata

class Jpeg:
    def __init__(self):
        self.image = Image()

    def addMetadata(self, asset, blob, metadata):
        self.image.addMetadata(asset, blob, metadata)
        metadata['jpeg'] = {}
        return metadata

class Gif:
    def __init__(self):
        self.image = Image()

    def addMetadata(self, asset, blob, metadata):
        self.image.addMetadata(asset, blob, metadata)
        metadata['gif'] = {}
        return metadata

typeIndex = {}
typeIndex['text/plain'] = Text()
typeIndex['application/javascript'] = Text()
typeIndex['text/x-python'] = Text()
typeIndex['text/markdown'] = Markdown()
typeIndex['image/png'] = Png()
typeIndex['image/jpeg'] = Jpeg()
typeIndex['image/gif'] = Gif()

class Asset:
    def __init__(self, id, xid, name):
        self.xid = str(xid)
        self.name = name
        self.versions = [str(id)]

        ext = os.path.splitext(name)[1]
        if ext in mimetypes.types_map:
            self.type = mimetypes.types_map[ext]
        elif ext in otherTypes:
            self.type = otherTypes[ext]
        else:
            self.type = ''

    def addVersion(self, id):
        latest = self.versions[-1]
        if (id != latest):
            self.versions.append(str(id))

    def prevLink(self, id):
        i = self.versions.index(str(id))
        if i > 0:
            prev = self.versions[i-1]
            return createLink(self.xid, prev)
        else:
            return ''

    def metadata(self, blob):
        data = {}
        data['xidb'] = {
            'xid': self.xid,
            'snapshot': '',
            'prev': self.prevLink(blob.id),
            'next': '',
            'type': self.type,
            'link': createLink(self.xid, blob.id),
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

    def add(self, id, asset):
        self.assets[asset.xid] = {
            'name': asset.name,
            'commit': str(self.commit.id),
            'oid': str(id)
        }

    def __str__(self):
        return "snapshot %s at %s" % (self.link, self.timestamp)

    def metadata(self):
        data = {}
        data['xidb'] = {
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
        self.saveIndex() # until javascript can generate xid

    def genxid(self):
        walker = self.repo.walk(self.repo.head.target, GIT_SORT_TIME | GIT_SORT_REVERSE)
        commit = walker.next()
        xid = genxid(commit.id, commit.tree.id)
        return str(xid)

    def init(self): 
        self.initSnapshots()
        self.initMetadata(True)
        self.saveSnapshots()

    def update(self):
        self.updateSnapshots()
        self.initMetadata()
        self.saveSnapshots()

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
        self.loadSnapshots(True)

    def loadSnapshots(self, rewrite=False):
        for snapshot in self.snapshots:
            if not rewrite and os.path.exists(snapshot.path):
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
                metadata = snapshot.metadata()
                metadata['xidb']['project'] = self.xid
                self.snapshotsCreated += 1

    def saveSnapshots(self):
        for snapshot in self.snapshots:
            saveFile(snapshot.path, snapshot.metadata())
            print "saved snapshot", snapshot.path

    def initMetadata(self, rewrite=False):
        prevSnapshot = None
        for snapshot in self.snapshots:
            for xid in snapshot.assets:
                info = snapshot.assets[xid]
                name = info['name']
                oid = info['oid']

                try:
                    blob = self.repo[oid]
                except:
                    print "bad blob?", info
                    continue

                if blob.type != GIT_OBJ_BLOB:
                    continue

                prev = None
                if prevSnapshot:
                    if xid in prevSnapshot.assets:
                        prev = prevSnapshot.assets[xid]
                        print ">>> found", xid, oid, prev['oid']
                        if oid == prev['oid']:
                            info['commit'] = prev['commit']
                            print "same version! resetting commit"
                            continue

                link = createLink(xid, snapshot.commit.id)
                path = self.createPath(link)
                asset = self.assets[name]

                if rewrite or not os.path.isfile(path):
                    metadata = asset.metadata(blob)
                    metadata['xidb']['link'] = link
                    if prev:
                        metadata['xidb']['prev'] = createLink(xid, prev['commit'])
                    else:
                        metadata['xidb']['prev'] = ''

                    metadata['xidb']['snapshot'] = snapshot.link
                    metadata['xidb']['timestamp'] = snapshot.timestamp
                        
                    saveFile(path, metadata)
                    print "wrote metadata for", link, name
                    self.assetsCreated += 1

                    prevLink = asset.prevLink(blob.id)
                    prevPath = self.createPath(prevLink)
                    if os.path.isfile(prevPath):
                        with open(prevPath) as f:
                            meta = json.loads(f.read())
                        meta['xidb']['next'] = link
                        saveFile(prevPath, meta)

            prevSnapshot = snapshot
