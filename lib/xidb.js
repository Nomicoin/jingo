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
  var index = path.join(this.metaDir, 'index.json');
  var data = fs.readFileSync(index);
  var parsed = JSON.parse(data);
  var projects = parsed['projects'];
  var xid = projects[repo];

  return xid;
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
  var snapshot = JSON.parse(data);
  var assets = snapshot['assets'];

  var files = [];

  for(xid in assets) {
    var asset = assets[xid];
    var oid = asset.oid;
    var commit = asset.commit;
    var name = asset.name;
    var link = this.createLink(xid, commit);
    files.push({'commit':commit, 'xid':xid, 'oid':oid, 'name':name, 'link':link});
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

Xidb.prototype.getMetaVersions = function(xid) {
  var dataPath = path.join(this.metaDir, xid.slice(0,8));
  var files = fs.readdirSync(dataPath);
  var self = this;

  var versions = files.map(function(file) {
    var versionPath = path.join(dataPath, file);
    var versionData = fs.readFileSync(versionPath);
    var versionMetadata = JSON.parse(versionData).xidb;

    if (versionMetadata.snapshot) {
      var snapshotLink = versionMetadata.snapshot;
      var snapshotPath = self.createPathFromLink(snapshotLink);
      var snapshotData = fs.readFileSync(snapshotPath);
      var snapshotMetadata = JSON.parse(snapshotData);

      // Resolving an xlink means replacing the link with the content it references.
      // TODO: add an xidb function to do this in a general manner
      versionMetadata.snapshot = snapshotMetadata.xidb;
    }
    else {
      // A snapshot is its own snapshot
      versionMetadata['snapshot'] = versionMetadata;
    }

    return versionMetadata;
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
    var vlink = versions[i].link;

    if (i == 0) {
      first = vlink;
    }

    if (i == count-1) {
      last = vlink;
    }

    if (vlink == link) {
      version = i+1;

      if (i > 0) {
	prev = versions[i-1].link;
      }

      if (i < count-1) {
	next = versions[i+1].link;
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

  //metadata['navigation'] = this.getNavLinks(xid, cid);

  return metadata;
}

Xidb.prototype.getMetadata = function(xid, cid) {
  var dataPath = this.createPath(xid, cid);
  var data = fs.readFileSync(dataPath);
  var metadata = JSON.parse(data);

  metadata['navigation'] = this.getNavLinks(xid, cid);

  return metadata;
}


module.exports = new Xidb();
