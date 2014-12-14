var fs = require('fs');
var path = require('path');
var Configurable = require("./configurable");
var moment = require("moment");
var exec = require("child_process").exec;

var Xidb = function () {
  Configurable.call(this);

  var config = this.getConfig().application;
  this.wikiDir = config.repository;
  this.wikiGitDir = path.join(config.repository, ".git/");
  this.guildDir = config.guild;
  this.guildGitDir = path.join(config.guild, ".git/");
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

Xidb.prototype.getSnapshot = function(repoDir, commitId) {
  var projectId = this.getProjectId(repoDir, commitId);
  var snapshotPath = this.createPath(projectId, commitId);
  var data = fs.readFileSync(snapshotPath);
  var snapshot = JSON.parse(data);

  return snapshot;
}

Xidb.prototype.getWikiSnapshot = function(cid) {
  return this.getSnapshot(this.wikiGitDir, cid);
}

Xidb.prototype.getLatestWikiSnapshot = function() {
  var commitId = this.getHeadCommit(this.wikiGitDir);
  return this.getSnapshot(this.wikiGitDir, commitId);
}

Xidb.prototype.getGuildSnapshot = function(cid) {
  return this.getSnapshot(this.guildGitDir, cid);
}

Xidb.prototype.getLatestGuildSnapshot = function() {
  var commitId = this.getHeadCommit(this.guildGitDir);
  return this.getSnapshot(this.guildGitDir, commitId);
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

Xidb.prototype.getComments = function(xlink) {
  var metadata = this.getMetadataFromLink(xlink);
  var comments = metadata.base.comments;
  var self = this;

  if (comments) {
    comments = comments.map(function(clink) {
      var metadata = self.getMetadataFromLink(clink);
      var age = moment(metadata.base.timestamp).fromNow();

      metadata.comment.authorLink = "/view/" + metadata.comment.author;
      metadata.comment.age = age;
      metadata.comment.link = "/meta/" + metadata.base.xlink + "/asset";

      return metadata;
    });

    comments.sort(function(a,b) {
      return a.base.timestamp.localeCompare(b.base.timestamp);
    });
  }

  return comments;
}

Xidb.prototype.getVotes = function(xlink) {
  var metadata = this.getMetadataFromLink(xlink);
  console.log(metadata.base.votes);

  var votes = [];

  for(var xid in metadata.base.votes) {
    var vlink = metadata.base.votes[xid];
    var metavote = this.getMetadataFromLink(vlink);
    var author = this.getMetadataFromLink(metavote.vote.agent);

    metavote.author = author;
    metavote.author.link = "/view/" + metavote.vote.agent;
    metavote.vote.age = moment(metavote.base.timestamp).fromNow();
    metavote.vote.link = "/meta/" + vlink + "/asset";

    votes.push(metavote);
  }

  return votes;
}

Xidb.prototype.getVoteResults = function(metadata, votes) {
  var results = {
    'approvals': 0,
    'rejections': 0,
    'abstentions': 0,
    'result': 'pending',
    'timeLeft': 'unknown',
  };

  for (var i = 0; i < votes.length; i++) {
    var vote = votes[i];

    if (vote.vote.val == 1) {
      results.approvals += 1;
    }
    else if (vote.vote.val == 0) {
      results.rejections += 1;
    }
    else {
      results.abstentions += 1;
    }
  }

  return results;
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
  var command = "python addComment.py -a " + user.username + " -x " + xlink;

  child = exec(command, { cwd: this.scriptDir }, function(error, stdout, stderr) {
    if (error || stderr.length > 0) {
      error = new Error(command + "\n" + stderr);
      cb(error);
      return;
    }

    cb(null, stdout.toString());
  });

  child.stdin.write(comment);
  child.stdin.end();
}

Xidb.prototype.addVote = function(user, xlink, body, cb) {
  var command = "python addVote.py -a " + user.username + " -x " + xlink + " --vote " + body.vote;

  child = exec(command, { cwd: this.scriptDir }, function(error, stdout, stderr) {
    if (error || stderr.length > 0) {
      error = new Error(command + "\n" + stderr);
      cb(error);
      return;
    }

    cb(null, stdout.toString());
  });

  child.stdin.write(body.comment);
  child.stdin.end();
}

module.exports = new Xidb();
