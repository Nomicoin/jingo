var router = require("express").Router();
var renderer = require('../lib/renderer');
var xidb = require('../lib/xidb');
var fs = require("fs");

router.get("/api/v1/:xid/:oid*", _apiv1GetAsset);

router.get("/meta", _getMeta);
router.get("/meta/:xid", _getMetaIndex);
router.get("/meta/:xid/:oid", _getMetaPage);
router.get("/meta/:xid/:oid/:item*", _getMetaPageItem);
router.get("/meta/tree/:commit/:file", _getMetaPageTree);


function _apiv1GetAsset(req, res) {
  var xid = req.params.xid;
  var oid = req.params.oid;

  var metadata = xidb.getMetadata(xid, oid);

  console.log(">>> get asset", metadata.xidb.asset, metadata.xidb.type, metadata.xidb.size);

  Git.getBlob(metadata.xidb.asset, function(err, content) {
    res.writeHead(200, {'Content-Type': metadata.type });
    res.end(content);
    return;
  });
}

function _getMeta(req, res) {
  var assets = xidb.getAssets();

  res.render("meta", {
    title: "meta",
    files: assets
  });
}

function _getMetaIndex(req, res) {
  var xid = req.params.xid;
  var index = xidb.getMetadataIndex(xid);

  res.render("metaindex", {
    title: "index",
    versions: index
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
      link = "/meta/" + val;
    }
    else if (key == 'asset' && metadata['encoding'] == 'text') {
      link = "/meta/" + xid + "/" + oid + "/asset";
    }
    else if (key == 'xid') {
      link = "/meta/" + xid;
    }
    else if (key == 'name') {
      link = "/api/v1/"+ metadata.link + "/" + metadata.name;
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

    if (/\w{8}\/\w{8}/.test(val)) {
      res.redirect("/meta/" + val + rest);
      return;
    }

    if (item == 'asset') {

      Git.show(null, val, function(err, content) {
	var name = metadata['name'];
	res.render("raw", {
	  title: name,
	  content: content
	});
      });

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
