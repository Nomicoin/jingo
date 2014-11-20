var fs = require('fs');
var path = require('path');
var Configurable = require("./configurable");
var moment = require("moment");
var exec = require("child_process").exec;

var Xidb = function () {
  Configurable.call(this);

  var config = this.getConfig().application;
  this.repoDir = path.join(config.repository, ".git/");
  this.metaDir = path.join(config.guild, "meta");
  this.scriptDir = path.join(config.project, "scripts"); // tbd: change to config.viki
};

Xidb.prototype = Object.create(Configurable.prototype);

Xidb.prototype.getProjectList = function() {
  var index = path.join(this.metaDir, 'index.json');
  var data = fs.readFileSync(index);
  var parsed = JSON.parse(data);
  var projects = parsed['projects'];

  return projects;
}

Xidb.prototype.getProjectId = function(repo) {
  var projects = this.getProjectList();

  for (var name in projects) {
    var project = projects[name];
    if (project.repo == repo) {
      return project.xid;
    }
  }

  return null;
}

Xidb.prototype.createLink = function(xid, cid) {
  return path.join(xid.slice(0,8), cid.slice(0,8));
}

Xidb.prototype.createPathFromLink = function(link) {
  return path.join(this.metaDir, link) + '.json';
}

Xidb.prototype.createPath = function(xid, oid) {
  var link = this.createLink(xid, oid);
  return this.createPathFromLink(link);
}

Xidb.prototype.getHeadCommit = function(repoDir) {
  var head = fs.readFileSync(path.join(repoDir, 'HEAD'), 'utf-8');
  var ref = head.slice(5).trim();
  var commit = fs.readFileSync(path.join(repoDir, ref), 'utf-8');

  return commit.trim();
}

Xidb.prototype.getProjectIndex = function() {
  var projects = this.getProjectList();
  var index = [];

  for(var name in projects) {
    var project = projects[name];
    var cid = this.getHeadCommit(project.repo);
    var xlink = this.createLink(project.xid, cid);

    index.push({'name': name, 'xlink':xlink});
  }

  return index;
}

Xidb.prototype.getSnapshot = function(commitId) {
  var projectId = this.getProjectId(this.repoDir, commitId);
  var snapshotPath = this.createPath(projectId, commitId);
  var data = fs.readFileSync(snapshotPath);
  var snapshot = JSON.parse(data);

  return snapshot;
}

Xidb.prototype.getLatestSnapshot = function() {
  var commitId = this.getHeadCommit(this.repoDir);

  return this.getSnapshot(commitId);
}

Xidb.prototype.getMetalink = function(snapshot, name, ignoreCase) {
  var assets = snapshot.assets;

  for(xid in assets) {
    var asset = assets[xid];
    var assetName = asset.name;

    if (ignoreCase) {
      name = name.toUpperCase();
      assetName = assetName.toUpperCase();
    }

    if (name == assetName) {
      return this.createLink(xid, asset.commit);
    }
  }

  return null;
}

Xidb.prototype.getComments = function(snapshot, xlink) {
  var metadata = this.getMetadataFromLink(xlink);
  var assets = snapshot.assets;

  comments = [];
  for(var xid in assets) {
    var asset = assets[xid];
    if (asset.name.search("comments") == 0) {
      comments.push(this.createLink(xid, asset.commit));
    }
  }

  var self = this;
  comments = comments.map(function(clink) {
    var metadata = self.getMetadataFromLink(clink);
    var age = moment(metadata.base.timestamp).fromNow();
    //metadata.comment.authorName = metadata.comment.authorName;
    //metadata.comment.authorEmail = metadata.comment.authorEmail;
    metadata.comment.authorLink = "/meta/" + metadata.comment.author;
    metadata.comment.age = age;
    metadata.comment.link = "/meta/" + metadata.base.xlink + "/asset";
    return (metadata.comment.ref == xlink) ? metadata : null;
  });

  comments = comments.filter(function(metadata) { return metadata != null; });

  comments.sort(function(a,b) {
    return a.base.timestamp.localeCompare(b.base.timestamp);
  });

  //console.log(comments);

  return comments;
}

Xidb.prototype.resolveBranchLinks = function(versions) {
  var self = this;

  var resolved = versions.map(function(version) {
    if (version.branch) {
      var link = version.branch;
      var path = self.createPathFromLink(link);
      var data = fs.readFileSync(path);
      var metadata = JSON.parse(data);

      // Resolving an xlink means replacing the link with the content it references.
      // TODO: add an xidb function to do this in a general manner
      version.branch = {
	'base': metadata.base,
	'commit': metadata.commit
      };
    }

    return version;
  });

  return resolved;
}

Xidb.prototype.getMetaVersions = function(xid) {
  var dataPath = path.join(this.metaDir, xid.slice(0,8));
  var files = fs.readdirSync(dataPath);

  var versions = files.map(function(file) {
    var filePath = path.join(dataPath, file);
    var data = fs.readFileSync(filePath);
    var metadata = JSON.parse(data);

    return metadata.base;
  });

  versions.sort(function(a,b) {
    return a.timestamp.localeCompare(b.timestamp);
  });

  for (var i = 0; i < versions.length; i++) {
    versions[i]['version'] = i+1;
  }

  return versions;
}

Xidb.prototype.getNavLinks = function(xid, cid) {
  var versions = this.getMetaVersions(xid);
  var link = this.createLink(xid, cid);
  var first = '';
  var last = '';
  var next = '';
  var prev = '';
  var count = versions.length;
  var version = 0;

  for (var i = 0; i < count; i++) {
    var vlink = versions[i].xlink;

    if (i == 0) {
      first = vlink;
    }

    if (i == count-1) {
      last = vlink;
    }

    if (vlink == link) {
      version = i+1;

      if (i > 0) {
	prev = versions[i-1].xlink;
      }

      if (i < count-1) {
	next = versions[i+1].xlink;
      }
    }
  }

  return {
    'first':first,
    'next':next,
    'link':link,
    'prev':prev,
    'last':last,
    'version': '' + version + ' of ' + count
  };
}

Xidb.prototype.getMetadataFromLink = function(link) {
  var dataPath = this.createPathFromLink(link);
  var data = fs.readFileSync(dataPath);
  var metadata = JSON.parse(data);

  return metadata;
}

Xidb.prototype.getMetadata = function(xid, cid) {
  var dataPath = this.createPath(xid, cid);
  var data = fs.readFileSync(dataPath);
  var metadata = JSON.parse(data);

  metadata['navigation'] = this.getNavLinks(xid, cid);

  return metadata;
}

Xidb.prototype.getRepoDirFromBranch = function(branchLink) {
  var branch = this.getMetadataFromLink(branchLink);
  var projects = this.getProjectList();

  for(var name in projects) {
    var project = projects[name];
    if (project.xid == branch.base.xid) {
      return project.repo;
    }
  }

  return null;
}

Xidb.prototype.getBlob = function(branchLink, sha, cb) {
  var repoDir = this.getRepoDirFromBranch(branchLink);
  var prevDir = Git.setGitDir(repoDir);

  Git.getBlob(sha, function(err, content) {
    cb(err, content);
    Git.setGitDir(prevDir);
  });
}

Xidb.prototype.getUrl = function(xlink) {
  var metadata = this.getMetadataFromLink(xlink);

  // tbd: handle other types of docs
  return "/viki/" + metadata.markdown.page;
}

Xidb.prototype.addComment = function(user, xlink, comment, cb) {
  var command = "python addComment.py -a " + user.displayName + " -x " + xlink;

  child = exec(command, { cwd: this.scriptDir }, function(error, stdout, stderr) {
    if (error || stderr.length > 0) {
      error = new Error(commands + "\n" + stderr);
      cb(error);
      return;
    }

    cb(null, stdout.toString());
  });

  child.stdin.write(comment);
  child.stdin.end();
}

module.exports = new Xidb();
