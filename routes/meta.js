var router = require("express").Router();
var renderer = require('../lib/renderer');
var xidb = require('../lib/xidb');
var fs = require("fs");

router.get("/meta", _getMeta);
router.get("/meta/:xid/:oid", _getMetaPage);
router.get("/meta/tree/:commit/:file", _getMetaPageTree);
router.get("/meta/test/:commit/:path/:rest*?", _getMetaTest);

function _getMeta(req, res) {
  var assets = xidb.getAssets();

  res.render("meta", {
    title: "meta",
    files: assets
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

  if ('commit' in metadata) {
    metadata = metadata.commit;
  }
  else {
    metadata = metadata.xidb;
  }

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

function _getMetaTest(req, res) {

  var commit = req.params.commit;
  var path = req.params.path;
  var rest = req.params.rest;

  console.log(">>> _getMetaTest", commit, path, rest);

  res.redirect("/meta");
}


module.exports = router;
