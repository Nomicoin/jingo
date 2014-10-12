var router = require("express").Router();
var renderer = require('../lib/renderer');
var xidb = require('../lib/xidb');
var fs = require("fs");

var files = [];

function initFiles() {
  Git.ls("*", function(err, list) {

    console.log("\n\n>>>meta " + list.length + "\n\n");

    files = list.map(function(file) {
      return {
	name: file,
	path: Git.absPath(file),
	hash: 'pending'
      };
    });

    files.forEach(function(file) {
      Git.log(file.path, 'HEAD', function(err, metadata) {
	console.log(file.path, metadata);
	file.hash = metadata.fullhash.slice(0,8);
      });
    });
  });
}

initFiles();

router.get("/meta", _getMeta);
router.get("/meta/:commit/:file", _getMetaPage);

function _getMeta(req, res) {

  //console.log(files);

  res.render("meta", {
    title: "meta",
    files: files
  });
}

function _getMetaPage(req, res) {

  var commit = req.params.commit;
  var file = req.params.file;
  var metadata = xidb.getMetadata(commit, file);
  var page = "# metadata display page stub\n";

  for(key in metadata) {
    page += "* " + key + ": " + metadata[key] + "\n";
  }

  res.render("minimal", {
    title: "meta",
    content: renderer.render(page)
  });
}

module.exports = router;
