var router = require("express").Router();
var renderer = require('../lib/renderer');
var fs = require("fs");

var files = [];

function initFiles() {
  Git.ls("*", function(err, list) {

    console.log("\n\n>>>meta " + list.length + "\n\n");

    list.forEach(function(file) {
      var path = Git.absPath(file);
      Git.hashes(path, 1, function(err, hashes) {
	console.log(path, err, hashes);

	files.push({
	  name: file,
	  path: path,
	  hash: hashes[0]
	});
      });
    });
  });
}

initFiles();

router.get("/meta", _getMeta);

function _getMeta(req, res) {

  console.log(files);

  res.render("meta", {
    title: "meta",
    files: files
  });
}

module.exports = router;
