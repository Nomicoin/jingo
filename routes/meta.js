var router = require("express").Router();
var renderer = require('../lib/renderer');
var xidb = require('../lib/xidb');
var fs = require("fs");

router.get("/meta", _getMeta);
router.get("/meta/:xid/:oid", _getMetaPage);
router.get("/meta/:xid/:oid/:item*", _getMetaPageItem);
router.get("/meta/tree/:commit/:file", _getMetaPageTree);

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

  if ('xidb' in metadata) {
    metadata = metadata.xidb;
  }

  md = []

  for(key in metadata) {
    val = metadata[key];
    link = null;

    if (/\w{8}\/\w{8}/.test(val)) {
      link = val
    }
    md.push({'key':key, 'val':val, 'link':link});
  }

  res.render("metadata", {
    title: "metadata",
    metadata: md
  });
}

function _getMetaPageItem(req, res) {

  var xid = req.params.xid;
  var oid = req.params.oid;
  var item = req.params.item;
  var rest = req.params['0'];

  var metadata = xidb.getMetadata(xid, oid);

  if ('xidb' in metadata) {
    metadata = metadata.xidb;
  }

  if (item in metadata) {
    var val = metadata[item];

    console.log(">>>", item, val, metadata, rest);

    if (/\w{8}\/\w{8}/.test(val)) {
      res.redirect("/meta/" + val + rest);
      return;
    }

    res.render("metadata", {
      title: "metadata",
      metadata: [{ 'key':item, 'val':metadata[item], 'link':null }]
    });
  }
  else {
    res.redirect("/meta");
  }
}

function _getMetaPageTree(req, res) {

  var commit = req.params.commit;
  var file = req.params.file;
  var metalink = xidb.getMetalink(commit, file);

  res.redirect("/meta/" + metalink);
}

function _getMetaTest(req, res) {

  console.log(">>> _getMetaTest", req.url, req.params);

  res.redirect("/meta");
}


module.exports = router;
