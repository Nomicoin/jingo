var path = require("path"),
    Configurable = require("./configurable"),
    ecstatic = require("ecstatic");

var WikiStatic = function () {
  Configurable.call(this);
};

WikiStatic.prototype = Object.create(Configurable.prototype);

WikiStatic.prototype.configure = function () {
  var config = this.getConfig().application;

  // FIXME: figure out how to handle docSubdir here
  var wikiRoot = path.join(config.repository, config.docSubdir);
  var middleware = ecstatic({ root: wikiRoot, handleError: false });

  //console.log('wikiRoot = ' + wikiRoot);
  //console.log('absPath = ' + Git.absPath(''));

  return function(req, res, next) {
    console.log('>>> %s %s', req.method, req.url);

    if (req.url.match(/\.md$/)) {
      console.log('markdown file detected!');
      next();
    }
    else {
      middleware(req, res, next);
    }
  }
};

module.exports = new WikiStatic();
