import uuid, os, shutil, yaml, json, mimetypes, re
from pygit2 import *
from glob import glob
from datetime import datetime
from genxid import genxid
import xitypes


def createLink(xid, cid):
    xidRef = str(xid)[:8]
    cidRef = str(cid)[:8]
    return os.path.join(xidRef, cidRef)

def makeDirs(path):
    dirName = os.path.dirname(path)
    if not os.path.exists(dirName):
        os.makedirs(dirName)

def saveFile(path, data):
    makeDirs(path)
    with open(path, 'w') as f:
        f.write(data)

def saveJSON(path, obj):
    res = json.dumps(obj, sort_keys=True, indent=4, separators=(',', ': '))
    saveFile(path, res + "\n")

class Agent:
    @staticmethod
    def fromMetadata(meta):
        base = meta['base']
        xid = base['xid']
        xlink = base['xlink']

        asset = meta['asset']
        name = asset['name']
        email = os.path.basename(name)

        agent = Agent(email)
        agent.xid = xid
        agent.xlink = xlink
        agent.name = name

        return agent

    def __init__(self, email):
        self.email = email
        self.xid = '?'
        self.xlink = '?'
        self.name = 'nemo'

    def metadata(self, snapshot, type):
        data = {
            'base': {
                'xid': self.xid,
                'commit': str(snapshot.commit.id),
                'xlink': createLink(self.xid, snapshot.commit.id),
                'branch': snapshot.xlink,
                'timestamp': snapshot.timestamp,
                'ref': '',
                'type': type
            },
            'agent': {
                'name': self.name,
                'email': self.email,
            }
        }

        return data

class Asset:
    @staticmethod
    def fromMetadata(meta):
        base = meta['base']
        cid = base['commit']
        xid = base['xid']

        asset = meta['asset']
        sha = asset['sha']
        name = asset['name']

        return Asset(cid, sha, xid, name)

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
            # print "new version for", self.name, self.sha, sha
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
            obj = factory()
            obj.blob = blob
            obj.metadata = data
            obj.snapshot = snapshot
            obj.init()
            if obj.isValid():
                obj.addMetadata()
                break # use only first valid xitype
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
    def __init__(self, name, repoDir, metaDir):
        self.name = name
        self.repoDir = repoDir
        self.metaDir = metaDir
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

    def init(self, assets):
        """
        Generates metadata for all commits. Overwrites existing metadata.
        """
        self.assets = assets
        self.initSnapshots()
        self.initMetadata(True)
        self.saveSnapshots()

    def update(self, assets):
        """
        Generates metadata for all commits since the last update
        """
        self.assets = assets
        self.updateSnapshots()
        self.initMetadata()
        self.saveSnapshots()

    def createPath(self, xlink):
        """
        Returns file path to metadata at given xlink. Will create folders as a side effect.
        """
        path = os.path.join(self.metaDir, xlink) + ".json"
        makeDirs(path)
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
                        # print "Adding %s as %s" % (name, xid)
                        asset = Asset(commit, sha, xid, name)
                        self.assets[name] = asset
                    snapshot.add(asset)
                self.snapshotsLoaded += 1
            else:
                print "Building snapshot", snapshot.xlink
                self.addTree(snapshot.commit.tree, '', snapshot)
                self.snapshotsCreated += 1

    def saveSnapshots(self):
        schema = self.assets['xidb/types/branch']
        for snapshot in self.snapshots:
            data = snapshot.metadata()
            data['base']['type'] = schema.xlink if schema else ''
            saveJSON(snapshot.path, data)
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
                    saveJSON(path, metadata)
                    print "wrote metadata for", link, name
                    self.assetsCreated += 1

    def writeMetadata(self, meta):
        base = meta['base']
        xlink = base['xlink']
        path = self.createPath(xlink)
        saveJSON(path, meta)
        #print "writeMetadata", path, meta


class Guild:
    def __init__(self, config):
        self.wiki = config['application']['title']
        self.guildDir = config['application']['guild']
        self.metaDir = os.path.join(self.guildDir, "meta")
        self.repoDir = config['application']['repository']
        self.projDir = config['application']['project']

        self.name = os.path.basename(self.guildDir)
        self.project = os.path.basename(self.projDir)

        self.guildProject = Project(self.name, self.guildDir, self.metaDir)
        self.repoProject = Project(self.wiki, self.repoDir, self.metaDir)
        self.projProject = Project(self.project, self.projDir, self.metaDir)

        self.assets = {}

        if not os.path.exists(self.metaDir):
            os.makedirs(self.metaDir)

        self.indexPath = os.path.join(self.metaDir, "index.json")
        
        if os.path.exists(self.indexPath):
            with open(self.indexPath) as f:
                self.index = json.loads(f.read())
        else:
            self.index = {}

        self.agents = self.loadAgents()
        self.types = self.loadTypes()

    def getMetadata(self, xlink):
        path = self.repoProject.createPath(xlink)
        with open(path) as f:
            meta = json.loads(f.read())
        return meta

    def loadAgents(self):
        if not "agents" in self.index:
            return

        agents = {}
        index = self.index["agents"]
        for name in index:
            xlink = index[name]
            metadata = self.getMetadata(xlink)
            agent = Agent.fromMetadata(metadata)
            email = os.path.basename(name)
            agents[email] = agent
        return agents

    def loadTypes(self):
        types = {}
        return types
        
    def init(self):
        self.guildProject.init(self.assets)
        self.repoProject.init(self.assets)
        self.projProject.init(self.assets)
        self.saveIndex()

    def update(self):
        self.guildProject.update(self.assets)
        self.repoProject.update(self.assets)
        self.projProject.update(self.assets)
        self.saveIndex()

    def getAgent(self, email):
        if email in self.agents:
            return self.agents[email]

    def getAsset(self, xlink):
        path = self.repoProject.createPath(xlink)
        with open(path) as f:
            meta = json.loads(f.read())
        return Asset.fromMetadata(meta)

    def loadTypes(self):
        types = {}
        return types

    def addRef(self, meta, refType, xlink):
        base = meta['base']
        ref = base.get('ref') or {}
        section = ref.get(refType) or []
        section.append(xlink)
        ref[refType] = section
        base['ref'] = ref
        meta['base'] = base

    def addComment(self, email, xlink, comment):
        agent = self.getAgent(email)
        asset = self.getAsset(xlink)
        print "addComment", asset.name, asset.xlink
        print "agent:", agent.xid

        fileName = datetime.now().isoformat() + ".md"
        xidRef = agent.xid[:8]
        commentPath = os.path.join("comments", fileName) 
        fullPath = os.path.join(self.repoDir, commentPath)

        saveFile(fullPath, comment)

        repo = self.repoProject.repo
        index = repo.index

        index.read()
        index.add(commentPath)
        index.write()

        tree = index.write_tree()
        branch = 'refs/heads/test7'
        author = Signature(agent.name, agent.email)
        committer = author
        xaction = dict(author=agent.email, ref=asset.xlink, type="comment")
        message = json.dumps(xaction)
        cid = repo.create_commit(branch, author, committer, message, tree, [repo.head.target])

        self.update()
        commentAsset = self.assets[commentPath]

        print "agent xlink", agent.xlink
        agentMeta = self.getMetadata(agent.xlink)
        self.addRef(agentMeta, "comment", commentAsset.xlink)
        self.guildProject.writeMetadata(agentMeta)

        docMeta = self.getMetadata(xlink)
        self.addRef(docMeta, "comment", commentAsset.xlink)
        self.repoProject.writeMetadata(docMeta)

        return commentAsset.xlink

    def saveIndex(self):
        """
        Saves this project's info to an index file.
        """
        projects = {}
        for project in [self.guildProject, self.repoProject, self.projProject]:
            projects[project.name] = {
                "xid": project.xid,
                "repo": project.repo.path,
            }

        types = {}
        agents = {}

        for name in self.guildProject.assets:
            asset = self.guildProject.assets[name]
            #print name, asset.xlink
            if name.find("xidb/types") == 0:
                types[name] = asset.xlink
            if name.find("agents") == 0:
                agents[name] = asset.xlink

        saveJSON(self.indexPath, {"projects": projects, "types": types, "agents": agents})
