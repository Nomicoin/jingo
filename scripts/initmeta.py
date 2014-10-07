from pygit2 import *
import uuid

class Snapshot:
    def __init__(self, commit):
        self.commit = commit
        self.files = []
        for entry in commit.tree:
            self.files.append(entry)

class Project:
    def __init__(self):
        self.xid = uuid.uuid4()
    
    def init(self, repoDir):
        self.repo = Repository(repoDir)
        self.snapshots = []
        for commit in self.repo.walk(self.repo.head.target, GIT_SORT_TIME | GIT_SORT_REVERSE):
            self.snapshots.append(Snapshot(commit))

project = Project()
project.init('/home/david/dev/Meridion.wiki/.git')

for snapshot in project.snapshots:
    print snapshot.commit.id, len(snapshot.files)

print len(project.snapshots)





