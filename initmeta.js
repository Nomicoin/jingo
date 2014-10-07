var Promise = require('bluebird');
var git = Promise.promisifyAll(require('./lib/gitmech'));
var fs = require('fs');
var toml = require('toml-js');

function createGuid() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    var r = Math.random()*16|0, v = c == 'x' ? r : (r&0x3|0x8);
    return v.toString(16);
  });
}

var ProjectVersion = function(hash) {
  this.hash = hash;
}

var Project = function() {
  this.xid = createGuid();
};

Project.prototype.fetchHistory = function() {
  return new Promise(function(resolve, reject) {
    git.log(".", "HEAD", 10000, function(err, log) {
      this.history = log.reverse();
      resolve();
    }.bind(this));
  }.bind(this));
}

Project.prototype.fetchVersions = function() {
  return new Promise(function(resolve, reject) {
    for(var i = 0; i < this.history.length; i++) {
      this.history[i].version = new ProjectVersion(this.history[i].fullhash);
    }
    resolve();
  }.bind(this));
}

git.setup('', '/home/david/dev/Meridion.wiki', '', '', function(err, version) {

  if (err) {
    console.log(err);
    process.exit(-1);
  }

  var project = new Project();

  project.fetchHistory().then(function() {
    project.fetchVersions();
  }).then(function() {
    console.log(project);
  });

  // git.lsRev("*", "accffdc", function(err, list) {

  //   console.log(list.length + " files found\n\n");

  //   for(var i = 0; i < list.length; i++) {
  //     var file = list[i];
  //     console.log(file);
  //   }
  // });

});

