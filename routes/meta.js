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
router.get("/meta/:xid/:oid", _getMetaPage);
router.get("/meta/tree/:commit/:file", _getMetaPageTree);

function _getMeta(req, res) {

  //console.log(files);

  res.render("meta", {
    title: "meta",
    files: files
  });
}

function _makeWikiLink(text, link) {
  return "[" + text + "](" + link +")";
}

function _getMetaPage(req, res) {

  var xid = req.params.xid;
  var oid = req.params.oid;
  var metadata = xidb.getMetadata(xid, oid);
  var page = "# metadata display page stub\n";

  for(key in metadata) {
    val = metadata[key];

    if (/\w{8}\/\w{8}/.test(val)) {
      var link = "/meta/" + val;
      page += "* " + key + ": " + _makeWikiLink(val, link) +"\n";
    }
    else {
      page += "* " + key + ": " + val + "\n";
    }
  }

  res.render("minimal", {
    title: "meta",
    content: renderer.render(page)
  });
}

function _getMetaPageTree(req, res) {

  var commit = req.params.commit;
  var file = req.params.file;
  var metalink = xidb.getMetalink(commit, file);

  res.redirect("/meta/" + metalink);
}

module.exports = router;
