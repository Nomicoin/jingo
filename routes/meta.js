var router = require("express").Router();
var renderer = require('../lib/renderer');
var xidb = require('../lib/xidb');
var fs = require("fs");

router.get("/api/v1/asset/:xid/:oid*", _apiv1GetAsset);
router.get("/api/v1/meta/:xid/:oid*", _apiv1GetMetadata);

router.get("/meta", _getMeta);
router.get("/meta/:xid", _getMetaIndex);
router.get("/meta/:xid/:oid", _getMetaPage);
router.get("/meta/:xid/:oid/asset", _getAsset);
router.get("/meta/:xid/:oid/:item*", _getMetaPageItem);
router.get("/meta/tree/:commit/:file", _getMetaPageTree);


function _apiv1GetAsset(req, res) {
  var xid = req.params.xid;
  var oid = req.params.oid;

  var metadata = xidb.getMetadata(xid, oid);

  Git.getBlob(metadata.xidb.asset, function(err, content) {
    res.writeHead(200, {'Content-Type': metadata.type });
    res.end(content);
    return;
  });
}

function _apiv1GetMetadata(req, res) {
  var xid = req.params.xid;
  var oid = req.params.oid;

  var metadata = xidb.getMetadata(xid, oid);
  var content = JSON.stringify(metadata, null, 4);

  console.log(content);

  res.writeHead(200, {'Content-Type': 'application/json' });
  res.end(content);
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

function _getAsset(req, res) {
  var xid = req.params.xid;
  var oid = req.params.oid;
  var metadata = xidb.getMetadata(xid, oid).xidb;

  if (/image/.test(metadata.type)) {
    res.render("image", {
      'title': metadata.name,
      'link': "/api/v1/asset/" + metadata.link + "/" + metadata.name
    });
  }
  else {
    Git.getBlob(metadata.asset, function(err, content) {
      res.render("raw", {
	'title': metadata.name,
	'content': content
      });
    });
  }
}

function _getMetaPage(req, res) {
  var xid = req.params.xid;
  var oid = req.params.oid;
  var metadata = xidb.getMetadata(xid, oid);

  model = {}
  for(type in metadata) {
    md = [];
    section = metadata[type];
    
    for (key in section) {
      val = section[key];
      link = null;

      switch(key) {
      case 'link':
	link = "/api/v1/meta/" + val;
	break;

      case 'next':
      case 'prev':
      case 'xid':
      case 'snapshot':
	link = "/meta/" + val;
	break;

      case 'name':
	link = "/api/v1/asset/"+ section.link + "/" + section.name;
	break;

      case 'asset':
	link = "/meta/" + xid + "/" + oid + "/asset";
	break;	
      }

      md.push({'key':key, 'val':val, 'link':link});
    }

    model[type] = md;
  }

  res.render("metadata", {
    title: "metadata",
    metadata: model
  });
}

function _getMetaPageItem(req, res) {

  var xid = req.params.xid;
  var oid = req.params.oid;
  var item = req.params.item;
  var rest = req.params['0'];

  var metadata = xidb.getMetadata(xid, oid).xidb;

  if (!(item in metadata)) {
    res.redirect("/meta");
    return;
  }

  var val = metadata[item];

  console.log(">>>", metadata, item, val, rest);

  if (/\w{8}\/\w{8}/.test(val)) {
    res.redirect("/meta/" + val + rest);
    return;
  }

  res.render("metadata", {
    title: "metadata",
    metadata: {'metadatum': [{ 'key':item, 'val':val, 'link':null }]}
  });
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
