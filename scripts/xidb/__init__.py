import uuid, os, shutil, yaml, json, mimetypes, re
from pygit2 import *
from glob import glob
from datetime import datetime
from xidb.genxid import genxid
from xidb.xitypes import Agent, Asset
from xidb.utils import *

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
    def __init__(self, name, repoDir, metaDir, assets):
        self.name = name
        self.repoDir = repoDir
        self.metaDir = metaDir
        self.assets = assets
        self.repo = Repository(self.repoDir)
        self.xid = self.genxid()
        self.snapshots = []
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
        self.initMetadata()
        self.saveSnapshots()

    def update(self):
        """
        Generates metadata for all commits since the last update
        """
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
                    asset = Asset()
                    asset.configure(snapshot.commit.id, obj.id, xid, name)
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
        # load only snapshots since last update
        self.loadSnapshots()

    def initSnapshots(self):
        for commit in self.repo.walk(self.repo.head.target, GIT_SORT_TIME | GIT_SORT_REVERSE):
            link = createLink(self.xid, commit.id)
            path = self.createPath(link)
            snapshot = Snapshot(self.xid, commit, link, path)
            self.snapshots.append(snapshot)
        # load all snapshots in project
        self.loadSnapshots(True)

    def loadSnapshots(self, rewrite=False):
        self.newAssets = []
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
                        asset = Asset()
                        asset.configure(commit, sha, xid, name)
                        self.assets[name] = asset
                        self.newAssets.append(asset)
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

    def initMetadata(self):

        #assets = {asset.xlink: asset for xid, asset in assets.items()}

        self.newAssets = []

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
                    asset = asset.generate(blob, snapshot)
                    asset.save(path)
                    self.assets[name] = asset
                    self.newAssets.append(asset)
                    print "wrote metadata for", link, name, asset.typeName()
                    self.assetsCreated += 1

class Guild:
    def __init__(self, config, rebuild=False):
        self.wiki = config['application']['title']
        self.guildDir = config['application']['guild']
        self.metaDir = os.path.join(self.guildDir, "meta")
        self.repoDir = config['application']['repository']
        self.projDir = config['application']['project']

        self.name = os.path.basename(self.guildDir)
        self.project = os.path.basename(self.projDir)
        self.assets = {}

        self.guildProject = Project(self.name, self.guildDir, self.metaDir, self.assets)
        self.repoProject = Project(self.wiki, self.repoDir, self.metaDir, self.assets)
        self.projProject = Project(self.project, self.projDir, self.metaDir, self.assets)

        if rebuild:
            shutil.rmtree(self.metaDir, ignore_errors=True)

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
            meta['base']['path'] = path
        return meta

    def loadAgents(self):
        if not "agents" in self.index:
            return

        agents = {}
        index = self.index["agents"]
        for name in index:
            xlink = index[name]
            agent = self.agentFromXlink(xlink)
            id = os.path.basename(name)
            agents[id] = agent
        return agents

    def loadTypes(self):
        types = {}
        return types
        
    def init(self):
        self.guildProject.init()
        self.repoProject.init()
        self.projProject.init()
        self.connectAssets()
        self.saveIndex()

    def update(self):
        self.guildProject.update()
        self.repoProject.update()
        self.projProject.update()
        self.connectAssets()
        self.saveIndex()

    def connectAssets(self):
        assets = []
        assets.extend(self.guildProject.newAssets)
        assets.extend(self.repoProject.newAssets)
        assets.extend(self.projProject.newAssets)

        assets = sorted(assets, key=lambda asset: asset.getTimestamp())

        for asset in assets:
            asset.connect(self)

        print ">>> connectAssets", len(assets)

    def getAgent(self, id):
        id = id.lower()
        if id in self.agents:
            return self.agents[id]

    def getAsset(self, xlink, asset=Asset()):
        path = self.repoProject.createPath(xlink)
        with open(path) as f:
            meta = json.loads(f.read())
            meta['base']['path'] = path
        asset.initFromMetadata(meta)
        return asset

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

    def addComment(self, handle, xlink, comment):
        agent = self.getAgent(handle)
        return self.saveComment(agent, xlink, comment)

    def addRating(self, handle, xlink, val, min, max, comment):
        agent = self.getAgent(handle)
        val = float(val)
        min = int(min)
        max = int(max)
        rating = (val-min)/(max-min)
        eval = dict(agent=agent.getXlink(),
                    ref=xlink,
                    val=val,
                    min=min,
                    max=max,
                    rating=rating,
                    type="rating")

        evalLink = self.saveEval(agent, xlink, eval)
        self.saveComment(agent, evalLink, comment)
        return evalLink
        
    def addVote(self, handle, xlink, vote, comment):
        agent = self.getAgent(handle)

        min = 0
        max = 1

        vote = vote.lower()

        if vote in ["yes", "+1", "approve", "aye"]:
            val = max
        elif vote in ["no", "-1", "reject", "nay"]:
            val = min
        else:
            val = 0.5

        eval = dict(agent=agent.getXlink(),
                    ref=xlink,
                    type="vote",
                    comment=comment,
                    vote=vote,
                    val=val,
                    min=min,
                    max=max)
        evalLink = self.saveEval(agent, xlink, eval)
        #self.saveComment(agent, evalLink, comment)
        return evalLink

    def makeEvalPath(self, ext):
        fileName = datetime.now().isoformat() + ext
        fileName = fileName.replace("-","/")
        fileName = fileName.replace("T","/")
        return os.path.join("evals", fileName) 

    def saveEval(self, agent, xlink, eval):
        asset = self.getAsset(xlink)
        path = self.makeEvalPath(".json")
        fullPath = os.path.join(self.guildDir, path)

        saveJSON(fullPath, eval)
        return self.commitFile(self.guildProject.repo, agent, asset, eval['type'], path)

    def saveComment(self, agent, xlink, comment):
        asset = self.getAsset(xlink)
        path = self.makeEvalPath(".md")
        fullPath = os.path.join(self.guildDir, path)

        saveFile(fullPath, comment)
        return self.commitFile(self.guildProject.repo, agent, asset, "comment", path)

    def commitFile(self, repo, agent, asset, type, path):
        index = repo.index

        index.read()
        index.add(path)
        index.write()

        tree = index.write_tree()
        branch = repo.head.name
        author = agent.getSignature()
        committer = author #todo: should be this script agent
        xaction = dict(author=agent.getXlink(), ref=asset.xlink, type=type)
        message = json.dumps(xaction)
        cid = repo.create_commit(branch, author, committer, message, tree, [repo.head.target])

        self.update()
        newAsset = self.assets[path]
        return newAsset.xlink

    def agentFromXlink(self, xlink):
        meta = self.getMetadata(xlink)
        asset = meta['asset']
        sha = asset['sha']
        blob = self.guildProject.repo[sha]
        data = json.loads(blob.data)
        agent = Agent()
        agent.initFromMetadata(meta)
        agent.data = data
        return agent

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
            if name.find("agents/data") == 0:
                file = os.path.basename(name)
                handle, ext = os.path.splitext(file)
                agents[handle] = asset.xlink

        saveJSON(self.indexPath, {"projects": projects, "types": types, "agents": agents})
