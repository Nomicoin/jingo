var Configurable = require("./configurable");
var ecstatic = require("ecstatic");

var WikiStatic = function () {
  Configurable.call(this);
};

WikiStatic.prototype = Object.create(Configurable.prototype);

WikiStatic.prototype.configure = function () {

  var config = this.getConfig().application;

  console.log(config.repository);

  return ecstatic({ root: config.repository, handleError: false });
};

module.exports = new WikiStatic();
