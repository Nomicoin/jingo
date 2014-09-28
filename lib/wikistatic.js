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

  return ecstatic({ root: config.repository, handleError: false });
};

module.exports = new WikiStatic();
