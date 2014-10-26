var router = require("express").Router();
var renderer = require('../lib/renderer');
var xidb = require('../lib/xidb');
var fs = require("fs");

router.get("/api/v1/asset/:xid/:cid*", _apiv1GetAsset);
router.get("/api/v1/meta/:xid/:cid*", _apiv1GetMetadata);
router.get("/api/v1/versions/:xid*", _apiv1GetVersions);

router.get("/meta", _getMeta);
router.get("/meta/:xid", _getAssetVersions);
router.get("/meta/:xid/:cid", _getMetaPage);
router.get("/meta/:xid/:cid/asset", _getAsset);
router.get("/meta/:xid/:cid/branch", _getBranch);
router.get("/meta/:xid/:cid/:item*", _getMetaPageItem);
router.get("/meta/tree/:commit/:file", _getMetaPageTree);


function _apiv1GetAsset(req, res) {
  var xid = req.params.xid;
  var cid = req.params.cid;

  var metadata = xidb.getMetadata(xid, cid);

  xidb.getBlob(metadata.base.branch, metadata.asset.sha, function(err, content) {
    res.writeHead(200, {'Content-Type': metadata.type });
    res.end(content);
    return;
  });
}

function _apiv1GetMetadata(req, res) {
  var xid = req.params.xid;
  var cid = req.params.cid;

  var metadata = xidb.getMetadata(xid, cid);
  var content = JSON.stringify(metadata, null, 4);

  res.writeHead(200, {'Content-Type': 'application/json' });
  res.end(content);
}

function _apiv1GetVersions(req, res) {
  var xid = req.params.xid;
  var versions = xidb.getMetaVersions(xid);
  var content = JSON.stringify(versions, null, 4);

  res.writeHead(200, {'Content-Type': 'application/json' });
  res.end(content);
}

function _getMeta(req, res) {
  res.render("projindex", {
    'title': "projects",
    'index': xidb.getProjectIndex()
  });
}

function _getAssetVersions(req, res) {
  var xid = req.params.xid;
  var versions = xidb.getMetaVersions(xid);
  var latest = versions[versions.length-1];
  var metadata = xidb.getMetadataFromLink(latest.xlink);

  res.render("metaindex", {
    'title': "versions",
    'name': metadata.asset.name,
    'versions': xidb.resolveBranchLinks(versions)
  });
}

function _makeWikiLink(text, link) {
  return "[" + text + "](" + link +")";
}

function _getAsset(req, res) {
  var xid = req.params.xid;
  var cid = req.params.cid;
  var metadata = xidb.getMetadata(xid, cid);
  var snapshot = xidb.getMetadataFromLink(metadata.base.branch);

  if ('image' in metadata) {
    res.render("asset", {
      'title': metadata.asset.name,
      'imgsrc': "/api/v1/asset/" + metadata.base.xlink + "/" + metadata.asset.name,
      'nav': metadata.navigation,
      'snapshot': snapshot.commit
    });
  }
  else {
    xidb.getBlob(metadata.base.branch, metadata.asset.sha, function(err, content) {

      // TODO: figure out how to get jade to preserve spaces
      //var text = content.toString().replace(new RegExp(' ', 'g'), '&sp;');
      //var lines = text.split('\n');

      res.render("asset", {
	'title': metadata.asset.name,
	'content': content,
	//'lines': lines, 
	'nav': metadata.navigation,
	'snapshot': snapshot.commit
      });
    });
  }
}

function _addXidbLinks(section, xlink) {

  var md = [];

  for (key in section) {
    val = section[key];
    link = null;

    switch(key) {
    case 'xlink':
      link = "/api/v1/meta/" + val;
      break;

    case 'first':
    case 'last':
    case 'next':
    case 'prev':
    case 'xid':
    case 'snapshot':
    case 'type':
    case 'xlink':
      link = "/meta/" + val;
      break;

    case 'name':
      link = "/api/v1/asset/"+ xlink + "/" + val;
      break;

    case 'branch':
      link = "/meta/" + val + "/branch";
      break;

    case 'asset':
    case 'sha':
      link = "/meta/" + xlink + "/asset";
      break;
    }

    md.push({'key':key, 'val':val, 'link':link});
  }

  return md;
}

function _addAssetsLinks(section) {

  var md = [];

  for (key in section) {
    val = section[key];
    metaLink = xidb.createLink(key, val.commit);
    link = "/meta/" + metaLink;
    md.push({'key':val.name, 'val':metaLink, 'link':link});
  }

  md.sort(function(a,b) {
    return a.key.localeCompare(b.key);
  });

  return md;
}

function _getBranch(req, res) {
  var xid = req.params.xid;
  var cid = req.params.cid;
  var metadata = xidb.getMetadata(xid, cid);
  var assets = [];

  for(xid in metadata.assets) {
    var asset = metadata.assets[xid];
    assets.push({
      'name': asset.name,
      'xlink': xidb.createLink(xid, asset.commit)
    });
  }

  assets.sort(function(a,b) {
    return a.name.localeCompare(b.name);
  });

  res.render("branch", {
    title: "branch",
    commit: metadata.commit,
    assets: assets,
    nav: metadata.navigation
  });
}

function _getMetaPage(req, res) {
  var xid = req.params.xid;
  var cid = req.params.cid;
  var metadata = xidb.getMetadata(xid, cid);

  model = {}
  for(type in metadata) {
    section = metadata[type];

    switch(type) {
    case "assets":
      model[type] = _addAssetsLinks(section);
      break;

    default:
      model[type] = _addXidbLinks(section, metadata.base.xlink);
      break;
    }
  }

  res.render("metadata", {
    title: metadata.base.xlink,
    metadata: model
  });
}

function _getMetaPageItem(req, res) {

  var xid = req.params.xid;
  var cid = req.params.cid;
  var item = req.params.item;
  var rest = req.params['0'];

  var metadata = xidb.getMetadata(xid, cid).xidb;

  if (!(item in metadata)) {
    res.redirect("/meta");
    return;
  }

  var val = metadata[item];

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
