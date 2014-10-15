var toml = require('toml-js');
var fs = require('fs');
var path = require('path');
var Configurable = require("./configurable");

var Xidb = function () {
  Configurable.call(this);

  var config = this.getConfig().application;
  this.repoDir = path.join(config.repository, ".git/");
  this.metaDir = config.metadata;
};

Xidb.prototype = Object.create(Configurable.prototype);

Xidb.prototype.getProjectId = function(repo, cb) {
  var index = path.join(this.metaDir, 'index.toml');
  var data = fs.readFileSync(index);
  var parsed = toml.parse(data);
  var projects = parsed['projects'];
  var xid = projects[repo];

  return xid;
}

Xidb.prototype.createLink = function(xid, oid) {
  return path.join(xid.slice(0,8), oid.slice(0,8));
}

Xidb.prototype.createPath = function(xid, oid) {
  var link = this.createLink(xid, oid);
  return path.join(this.metaDir, link) + '.toml';
}

Xidb.prototype.getHeadCommit = function() {
  var head = fs.readFileSync(path.join(this.repoDir, 'HEAD'), 'utf-8');
  var ref = head.slice(5).trim();
  var commit = fs.readFileSync(path.join(this.repoDir, ref), 'utf-8');

  return commit.trim();
}

Xidb.prototype.getAssets = function(revision) {
  var commitId = revision || this.getHeadCommit();
  var projectId = this.getProjectId(this.repoDir, commitId);
  var snapshotPath = this.createPath(projectId, commitId);
  var data = fs.readFileSync(snapshotPath);
  var snapshot = toml.parse(data);
  var assets = snapshot['assets'];

  var files = [];

  for(oid in assets) {
    var asset = assets[oid];
    var xid = asset[0];
    var path = asset[1];
    var link = this.createLink(xid, oid);
    files.push({'commit':oid, 'xid':xid, 'name':path, 'link':link});
  }

  files.sort(function(a,b) { return a.name.localeCompare(b.name); });

  return files;
}

Xidb.prototype.getMetalink = function(commitId, name) {
  var assets = this.getAssets(commitId);

  for(oid in assets) {
    var asset = assets[oid];
    var xid = asset[0];
    var path = asset[1];

    if (name == path) {
      return this.createLink(xid, oid);
    }
  }

  return null;
}

Xidb.prototype.getMetadata = function(xid, oid) {
  var dataPath = this.createPath(xid, oid);
  var data = fs.readFileSync(dataPath);
  var metadata = toml.parse(data);

  return metadata;
}

module.exports = new Xidb();
