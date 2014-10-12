var toml = require('toml-js');
var fs = require('fs');
var path = require('path');
var Configurable = require("./configurable");

var Xidb = function () {
  Configurable.call(this);

  var config = this.getConfig().application;
  this.repoDir = config.repository + "/.git/";
};

Xidb.prototype = Object.create(Configurable.prototype);

function getProjectId(repo, cb) {
  var data = fs.readFileSync('meta/index.toml');
  var parsed = toml.parse(data);
  var projects = parsed['projects'];
  var xid = projects[repo];

  return xid;
}

function createPath(xid, oid) {
  return path.join('meta', xid.slice(0,8), oid.slice(0,8)) + '.toml';
}

Xidb.prototype.getMetadata = function(commitId, name) {
  var projectId = getProjectId(this.repoDir, commitId);
  var snapshotPath = createPath(projectId, commitId);
  var data = fs.readFileSync(snapshotPath);
  var snapshot = toml.parse(data);
  var assets = snapshot['assets'];

  for(oid in assets) {
    var asset = assets[oid];
    var xid = asset[0];
    var path = asset[1];

    if (name == path) {
      var dataPath = createPath(xid, oid);
      var data = fs.readFileSync(dataPath);
      var metadata = toml.parse(data);
      return metadata['xidb'];
    }
  }

  return null;
}

module.exports = new Xidb();
