var router = require("express").Router();
var renderer = require('../lib/renderer');
var xidb = require('../lib/xidb');
var fs = require("fs");
var moment = require("moment");
var path = require('path');

router.get("/api/v1/asset/:xid/:cid*", _apiv1GetAsset);
router.get("/api/v1/meta/:xid/:cid*", _apiv1GetMetadata);
router.get("/api/v1/versions/:xid*", _apiv1GetVersions);

router.get("/viki/*", _getPage);
router.get("/v/:version/*", _getVPage);

router.get("/meta", _getMeta);
router.get("/meta/:xid", _getAssetVersions);
router.get("/meta/:xid/:cid", _getMetaPage);
router.get("/meta/:xid/:cid/asset", _getAsset);
router.get("/meta/:xid/:cid/as/:format", _getAsFormat);
router.get("/meta/:xid/:cid/branch", _getBranch);

router.post("/comment/:xid/:cid", _newComment);

function _getPage(req, res) {
  var cid = _getHeadCommit('Meridion');
  var page = req.params['0'];
  var url = path.join("/v", cid.slice(0,8), page);

  res.redirect(url);
}

function _getVPage(req, res) {
  var cid = req.params.version;
  var page = req.params['0'];
  var file = page.replace(/ /g, "-") + '.md';
  var snapshot = xidb.getSnapshot(cid);
  var xlink = xidb.getMetalink(snapshot, file, true);

  if (xlink == null) {
    // check for legacy versioned URL
    cid = path.basename(page);
    snapshot = xidb.getSnapshot(cid);
    page = path.dirname(page);
    file = page.replace(/ /g, "-") + '.md';
    xlink = xidb.getMetalink(snapshot, file, true);

    if (xlink != null) {
      var ver = cid.slice(0,8);
      var url = path.join("/v", ver, page);
      res.redirect(url);
    }
    else {
      res.locals.title = "404 - Not found";
      res.statusCode = 404;
      res.render('404.jade');
    }

    return;
  }

  var metadata = xidb.getMetadataFromLink(xlink);
  var branch = xidb.getMetadataFromLink(metadata.base.branch);
  var content = metadata.as.html;
  var snapshot = xidb.getSnapshot(cid);
  var latestSnapshot = xidb.getLatestSnapshot();
  var latestXlink = xidb.getMetalink(latestSnapshot, file, true);
  var comments = xidb.getComments(latestSnapshot, xlink);
  var addComment = "/comment/" + xlink;
  var age;

  if (xlink != latestXlink) {
    age = moment(snapshot.commit.timestamp).fromNow();
  }
  else {
    age = "current";
  }

  console.log("\n\n>>>", cid, snapshot.commit.timestamp, metadata.base.timestamp);
  console.log("branch age:", moment(snapshot.commit.timestamp).fromNow());
  console.log("page age:", moment(metadata.base.timestamp).fromNow());
  console.log("\n\n");

  res.render("page", {
    'title': metadata.asset.title,
    'page': metadata,
    'commit': branch.commit,
    'age': age,
    'content': content,
    'comments': comments,
    'addCommentLink': addComment,
  });
}

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
  var versions = xidb.resolveBranchLinks(versions);

  console.log(versions);
  console.log(metadata.asset);

  res.render("versions", {
    'title': metadata.asset.title,
    'asset': metadata.asset,
    'name': metadata.asset.name,
    'versions': versions
  });
}

function _getHeadCommit(project) {
  var projects = xidb.getProjectList();

  for(var name in projects) {
    if (name == project) {
      return xidb.getHeadCommit(projects[name].repo);
    }
  }

  return null;
}

function _getAsFormat(req, res) {
  var xid = req.params.xid;
  var cid = req.params.cid;
  var format = req.params.format;
  var metadata = xidb.getMetadata(xid, cid);
  var branch = xidb.getMetadataFromLink(metadata.base.branch);
  var content = metadata.as[format];

  res.render("page", {
    'title': metadata.asset.title,
    'metadata': metadata,
    'commit': branch.commit,
    'content': content,
  });
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
    case 'ref':
    case 'author':
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

    case 'page':
      link = "/viki/"+ val;
      break;

    case 'plink':
      link = "/v/"+ val;
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

function _newComment(req, res) {
  var xid = req.params.xid;
  var cid = req.params.cid;
  var xlink = xidb.createLink(xid, cid);
  var url = xidb.getUrl(xlink);

  xidb.addComment(req.user.email, xlink, req.body.comment, function(err, link) {
    res.redirect(url + "#addComment");
  });
}

module.exports = router;
