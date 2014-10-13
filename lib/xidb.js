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
  var data = fs.readFileSync('meta/index.toml');
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

Xidb.prototype.getMetalink = function(commitId, name) {
  var projectId = this.getProjectId(this.repoDir, commitId);
  var snapshotPath = this.createPath(projectId, commitId);
  var data = fs.readFileSync(snapshotPath);
  var snapshot = toml.parse(data);
  var assets = snapshot['assets'];

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
