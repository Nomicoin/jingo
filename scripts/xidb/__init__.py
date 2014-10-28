import uuid, os, shutil, yaml, json, mimetypes, re
from pygit2 import *
from datetime import datetime
from genxid import genxid
import xitypes

def createLink(xid, cid):
    xidRef = str(xid)[:8]
    cidRef = str(cid)[:8]
    return os.path.join(xidRef, cidRef)

def saveFile(path, obj):
    with open(path, 'w') as f:
        res = json.dumps(obj, sort_keys=True, indent=4, separators=(',', ': '))
        f.write(res + "\n")

class Asset:
    def __init__(self, cid, sha, xid, name):
        self.xid = str(xid)
        self.name = name
        self.ext = os.path.splitext(name)[1]
        self.cid = str(cid)
        self.sha = str(sha)
        self.xlink = createLink(self.xid, self.cid)

    def addVersion(self, cid, sha):
        sha = str(sha)
        cid = str(cid)
        if (self.sha != sha):
            #print "new version for", self.name, self.sha, sha
            self.sha = sha
            self.cid = cid
            self.xlink = createLink(self.xid, self.cid)

    def metadata(self, blob, snapshot, type):
        data = {}

        data['base'] = {
            'xid': self.xid,
            'commit': str(snapshot.commit.id),
            'xlink': createLink(self.xid, snapshot.commit.id),
            'branch': snapshot.xlink,
            'timestamp': snapshot.timestamp,
            'ref': '',
            'type': type
        }

        data['asset'] = {
            'name': self.name,
            'ext': self.ext,
            'title': '',
            'description': '',
            'sha': str(blob.id), 
            'size': blob.size,
            'encoding': 'binary' if blob.is_binary else 'text',
        }

        for factory in xitypes.allTypes:
            obj = factory(blob, data)
            if obj.isValid():
                obj.addMetadata()

        return data

class Snapshot:
    def __init__(self, xid, commit, link, path):
        self.xid = xid
        self.commit = commit
        self.xlink = link
        self.path = path
        self.timestamp = datetime.fromtimestamp(commit.commit_time).isoformat()
        self.assets = {}

    def __str__(self):
        return "snapshot %s at %s" % (self.xlink, self.timestamp)

    def add(self, asset):
        self.assets[asset.xid] = {
            'name': asset.name,
            'commit': asset.cid,
            'sha': asset.sha
        }

    def metadata(self):
        data = {}

        data['base'] = {
            'xid': self.xid,
            'xlink': self.xlink,
            'branch': self.xlink,
            'commit': str(self.commit.id),
            'timestamp': self.timestamp,
            'ref': '',
        }

        data['commit'] = {
            'commit': str(self.commit.id),
            'author': self.commit.author.name,
            'email': self.commit.author.email,
            'timestamp': self.timestamp,
            'message': self.commit.message,
        }

        data['assets'] = self.assets

        return data

class Project:
    def __init__(self, config):
        self.name = config['application']['title']
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
        """ 
        The project xid is generated from the first commit and tree sha's
        """
        walker = self.repo.walk(self.repo.head.target, GIT_SORT_TIME | GIT_SORT_REVERSE)
        commit = walker.next()
        xid = genxid(commit.id, commit.tree.id)
        return str(xid)

    def init(self): 
        """ 
        Generates metadata for all commits. Overwrites existing metadata.
        """
        self.initSnapshots()
        self.initMetadata(True)
        self.saveSnapshots()
        self.saveIndex()

    def update(self):
        """ 
        Generates metadata for all commits since the last update 
        """
        self.updateSnapshots()
        self.initMetadata()
        self.saveSnapshots()
        self.saveIndex()

    def saveIndex(self):
        """
        Saves this project's info to an index file.
        """
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

        projects[self.name] = {
            'xid': self.xid,
            'repo': self.repo.path,
        };

        saveFile(path, {'projects': projects})

    def createPath(self, xlink):
        """ 
        Returns file path to metadata at given xlink. Will create folders as a side effect.
        """
        path = os.path.join(self.metaDir, xlink) + ".json"
        dirName = os.path.dirname(path)
        if not os.path.exists(dirName):
            os.makedirs(dirName)
        return path

    def addTree(self, tree, path, snapshot):
        """
        Recursively traverses the git tree
        """
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
            snapshot = Snapshot(self.xid, commit, link, path)
            self.snapshots.insert(0, snapshot)
            if os.path.exists(path):
                break
        self.loadSnapshots()

    def initSnapshots(self):
        for commit in self.repo.walk(self.repo.head.target, GIT_SORT_TIME | GIT_SORT_REVERSE):
            link = createLink(self.xid, commit.id)
            path = self.createPath(link)
            snapshot = Snapshot(self.xid, commit, link, path)
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
                    sha = info['sha']
                    if name in self.assets:
                        asset = self.assets[name]
                        asset.addVersion(snapshot.commit.id, sha)
                    else:
                        #print "Adding %s as %s" % (name, xid)
                        asset = Asset(commit, sha, xid, name)
                        self.assets[name] = asset
                    snapshot.add(asset)
                self.snapshotsLoaded += 1
            else:
                print "Building snapshot", snapshot.xlink
                self.addTree(snapshot.commit.tree, '', snapshot)
                #metadata = snapshot.metadata()
                #metadata['xidb']['project'] = self.xid
                self.snapshotsCreated += 1

    def saveSnapshots(self):
        schema = self.assets['xidb/types/branch']
        for snapshot in self.snapshots:
            data = snapshot.metadata()
            data['base']['type'] = schema.xlink if schema else ''
            saveFile(snapshot.path, data)
            print "saved snapshot", snapshot.path

    def getType(self, name):
        schema = self.assets['xidb/types/asset']

        if re.match('xidb\/types\/.*', name):
            schema = self.assets['xidb/types/schema']
        elif re.search('\.png$', name):
            schema = self.assets['xidb/types/png']
        elif re.search('\.md$', name):
            schema = self.assets['xidb/types/markdown']

        return schema.xlink if schema else '?'

    def initMetadata(self, rewrite=False):
        for snapshot in self.snapshots:
            for xid in snapshot.assets:
                info = snapshot.assets[xid]
                name = info['name']
                sha = info['sha']
                cid = info['commit']

                try:
                    blob = self.repo[sha]
                except:
                    print "bad blob?", info
                    continue

                if blob.type != GIT_OBJ_BLOB:
                    continue

                link = createLink(xid, cid)
                path = self.createPath(link)
                asset = self.assets[name]

                if not os.path.isfile(path):
                    type = self.getType(asset.name)
                    metadata = asset.metadata(blob, snapshot, type)
                    saveFile(path, metadata)
                    print "wrote metadata for", link, name
                    self.assetsCreated += 1
