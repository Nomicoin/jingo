var router = require("express").Router();
var renderer = require('../lib/renderer');
var xidb = require('../lib/xidb');
var assets = require('../lib/assets');
var ui = require('../lib/ui');
var fs = require("fs");
var moment = require("moment");
var path = require('path');

router.get("/api/v1/asset/:xid/:cid*", _apiv1GetAsset);
router.get("/api/v1/meta/:xid/:cid*", _apiv1GetMetadata);
router.get("/api/v1/versions/:xid*", _apiv1GetVersions);

// wiki pages
router.get("/", _getIndex);
router.get("/wiki/:page", _redirectJingo);
router.get("/vpage/:xid/:cid", _viewPage);
router.get("/viki/:page/compare/:revisions", _getCompare);
router.get("/viki/history/:wiki/*", _getPageHistory);
router.get("/viki/:wiki/*", _getPage);
router.get("/v/:wiki/:version/*", _getVPage);
router.get("/history/:wiki", _getHistory);
router.get("/list/:wiki", _listAll);
router.get("/new/page", _newPage);
router.get("/versions/:xid", _getPageVersions);

// metadata
router.get("/view/:xid/:cid", _viewAsset);
router.get("/edit/:xid/:cid", _editAsset);
router.post("/save/:xid/:cid", _saveAsset);
router.put("/save/new/markdown", _saveNewMarkdown);
router.put("/save/:xid/:cid/markdown", _saveMarkdown);

router.get("/meta", _getMeta);
router.get("/meta/:xid", _getAssetVersions);
router.get("/meta/:xid/:cid", _getMetaPage);
router.get("/meta/:xid/:cid/as/:format", _getAsFormat);

router.get("/branch/:xid/:cid", _getBranch);
router.get("/snapshot/:xid/:cid", _getSnapshot);

router.post("/comment/:xid/:cid", _newComment);
router.post("/vote/:xid/:cid", _newVote);

function _redirectJingo(req, res) {
  var url = "/viki/wiki/" + req.params.page;
  res.redirect(url);
}

function _viewPage(req, res) {
  var xid = req.params.xid;
  var cid = req.params.cid;
  var xlink = xidb.createLink(xid, cid);
  var metadata = xidb.getMetadataFromLink(xlink);
  var url = "/v/wiki/" + cid + "/" + metadata.markdown.page;

  console.log(">>> _viewPage", xlink, metadata);
  console.log(">>> redirecting to", url);

  res.redirect(url);
}

function _getIndex(req, res) {
  res.redirect("/viki/wiki/Home");
}

function _newPage(req, res) {
  res.render("page-new", {
    'title': "new page",
  });
}

function _getPageHistory(req, res) {
  var wiki = req.params.wiki;
  var page = req.params['0'];
  var file = page.replace(/ /g, "-") + '.md';
  var repoDir = xidb.getRepoGitDir(wiki);
  var cid = xidb.getHeadCommit(repoDir);
  var snapshot = xidb.getWikiSnapshot(wiki, cid);
  var xlink = xidb.getMetalink(snapshot, file, true);
  var metadata = xidb.getMetadataFromLink(xlink);

  //console.log(">>> _getPageHistory", wiki, page, xlink, metadata);

  res.redirect("/versions/" + metadata.base.xid);
}

function _getPage(req, res) {
  var wiki = req.params.wiki;
  var repoDir = xidb.getRepoGitDir(wiki);
  var cid = xidb.getHeadCommit(repoDir);
  var page = req.params['0'];
  var url = path.join("/v", wiki, cid.slice(0,8), page);

  console.log(">>> redirecting to", url);

  res.redirect(url);
}

function _getVPage(req, res) {
  var wiki = req.params.wiki;
  var cid = req.params.version;
  var page = req.params['0'];
  var file = page.replace(/ /g, "-") + '.md';
  var snapshot = xidb.getWikiSnapshot(wiki, cid);
  var xlink = xidb.getMetalink(snapshot, file, true);
 
  if (xlink == null) {
    // check for legacy versioned URL
    console.log(">>> check for legacy versioned URL");

    cid = path.basename(page);
    snapshot = xidb.getWikiSnapshot(wiki, cid);

    if (snapshot == null) {
      var pageTitle = page.replace("-", " ");

      res.render("page-new.jade", {
	'title': "New page",
	'pageTitle': pageTitle,
      });

      return;
    }

    page = path.dirname(page);
    file = page.replace(/ /g, "-") + '.md';
    xlink = xidb.getMetalink(snapshot, file, true);

    if (xlink != null) {
      var ver = cid.slice(0,8);
      var url = path.join("/v", wiki, ver, page);
      res.redirect(url);
    }
    else {
      console.log(">>> 404 not found");

      res.locals.title = "404 - Not found";
      res.statusCode = 404;
      res.render('404.jade');
    }

    return;
  }

  var metadata = xidb.getMetadataFromLink(xlink);
  var branch = xidb.getMetadataFromLink(metadata.base.branch);
  var repo = xidb.getBranchRepo(metadata.base.branch);
  var content = metadata.as.html;
  var snapshot = xidb.getWikiSnapshot(wiki, cid);
  var latestSnapshot = xidb.getLatestWikiSnapshot(wiki);
  var latestXlink = xidb.getMetalink(latestSnapshot, file, true);
  var comments = xidb.getComments(xlink);
  var votes = xidb.getVotes(xlink);
  var voteResults = xidb.getVoteResults(metadata, votes);
  var age;

  if (xlink != latestXlink) {
    age = moment(snapshot.commit.timestamp).fromNow();
  }
  else {
    age = "current";
  }

  console.log(">>> _getVPage", metadata);

  res.locals.canEdit = true;

  res.render("page", {
    'title': metadata.asset.title,
    'page': metadata,
    'repo': repo,
    'commit': branch.commit,
    'age': age,
    'content': content,
    'comments': comments,
    'commentLink': "/comment/" + xlink,
    'votes': votes,
    'voteResults': voteResults,
    'voteLink': "/vote/" + xlink,
  });
}

function _getHistory(req, res) {
  var wiki = req.params.wiki;
  var repoDir = xidb.getRepoGitDir(wiki);
  var cid = xidb.getHeadCommit(repoDir);
  var snapshot = xidb.getWikiSnapshot(wiki, cid);

  console.log("_getHistory", wiki, repoDir, cid);
  //console.log(snapshot);

  var items = [];

  for(var xid in snapshot.assets) {
    //console.log(xid);
    var asset = snapshot.assets[xid];
    //console.log(asset);
    var metadata = xidb.getMetadata(xid, asset.commit);
    //console.log(metadata);

    console.log(metadata.base.commit, cid);

    if (cid == metadata.base.commit) {
      items.push(metadata);
    }
  }

  items.sort(function(a,b) {
    return a.base.timestamp.localeCompare(b.base.timestamp);
  });
  
  console.log(items);

  _getIndex(req, res);
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

function _getPageVersions(req, res) {
  var xid = req.params.xid;
  var versions = xidb.getMetaVersions(xid).reverse();
  var latest = versions[0];
  var metadata = xidb.getMetadataFromLink(latest.xlink);
  var versions = xidb.resolveBranchLinks(versions);

  //console.log(versions);

  res.render("revisions", {
    'title': metadata.asset.title,
    'name': metadata.asset.name,
    'versions': versions
  });
}

function _getAssetVersions(req, res) {
  var xid = req.params.xid;
  var versions = xidb.getMetaVersions(xid);
  var latest = versions[versions.length-1];
  var metadata = xidb.getMetadataFromLink(latest.xlink);
  var versions = xidb.resolveBranchLinks(versions);
  var repo = xidb.getBranchRepo(metadata.base.branch);

  console.log(versions);

  res.render("versions", {
    'title': metadata.asset.title,
    'asset': metadata.asset,
    'name': metadata.asset.name,
    'repo': repo,
    'versions': versions
  });
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

function _viewAsset(req, res) {
  var xid = req.params.xid;
  var cid = req.params.cid;
  var metadata = xidb.getMetadata(xid, cid);
  var snapshot = xidb.getMetadataFromLink(metadata.base.branch);

  if ('image' in metadata) {
    res.render("asset", {
      'title': metadata.asset.name,
      'imgsrc': "/api/v1/asset/" + metadata.base.xlink + "/" + metadata.asset.name,
      'metadata': metadata,
      'snapshot': snapshot.commit
    });
  }
  else {
    xidb.getBlob(metadata.base.branch, metadata.asset.sha, function(err, data) {
      var asset = assets.createAsset(data, metadata);
      var view = asset.getView();

      console.log(">>>", view);

      res.render(view, {
	'title': metadata.asset.title,
	'asset': asset,
	'content': data,
	'metadata': metadata,
	'snapshot': snapshot.commit
      });
    });
  }
}

function _editAsset(req, res) {
  var xid = req.params.xid;
  var cid = req.params.cid;
  var metadata = xidb.getMetadata(xid, cid);
  var snapshot = xidb.getMetadataFromLink(metadata.base.branch);

  console.log("_editAsset", metadata);

  xidb.getBlob(metadata.base.branch, metadata.asset.sha, function(err, data) {
    var asset = assets.createAsset(data, metadata);
    var editor = asset.getEditor();

    console.log(">>> editor=", editor);

    res.render(editor, {
      'title': metadata.asset.title,
      'asset': asset,
      'content': data,
      'metadata': metadata,
      'snapshot': snapshot.commit
    });
  });
}

function _form2json(body) {
  var data = {};

  for(var key in body) {
    var val = body[key];
    var keys = key.split('.');
    var node = data;

    for (var i = 0; i < keys.length; i++) {
      var subkey = keys[i];

      if (i == keys.length-1) {
	node[subkey] = val;
      }
      else {
	if (subkey in node) {
	  node = node[subkey];
	}
	else {
	  node[subkey] = {};
	  node = node[subkey];
	}
      }
    }
  }

  return JSON.stringify(data, null, 4);
}

function _saveAsset(req, res) {
  var xid = req.params.xid;
  var cid = req.params.cid;
  var xlink = xidb.createLink(xid, cid);
  var content = _form2json(req.body);

  //console.log(">>> saveAsset", xlink, content);

  xidb.saveAsset(req.user, xlink, content, function(err, newLink) {
    if (err) {
      console.log(err);
      res.redirect('/view/' + xlink);
    }
    else {
      console.log(">>> newLink", newLink);
      res.redirect('/view/' + newLink);
    }
  });
}

function _saveNewMarkdown(req, res) {
  var page = JSON.stringify(req.body, null, 4);

  console.log(">>> saveNewMarkdown", page);

  xidb.savePage(req.user, 'tbd', page, function(err, newLink) {
    if (err) {
      console.log(err);
      res.redirect('/view/' + xlink);
    }
    else {
      console.log(">>> newLink", newLink);
      res.redirect('/vpage/' + newLink);
    }
  });
}

function _saveMarkdown(req, res) {
  var xid = req.params.xid;
  var cid = req.params.cid;
  var xlink = xidb.createLink(xid, cid);
  var page = JSON.stringify(req.body, null, 4);

  console.log(">>> saveMarkdown", xlink, page);

  xidb.savePage(req.user, xlink, page, function(err, newLink) {
    if (err) {
      console.log(err);
      res.redirect('/view/' + xlink);
    }
    else {
      console.log(">>> newLink", newLink);
      res.redirect('/vpage/' + newLink);
    }
  });
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
      link = "/branch/" + val;
      break;

    case 'asset':
    case 'sha':
      link = "/view/" + xlink;
      break;

    case 'page':
      link = "/viki/wiki/"+ val;
      break;

    case 'plink':
      link = "/v/wiki/"+ val;
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

function _listAll(req, res) {
  var wiki = req.params.wiki;
  var projects = xidb.getProjectIndex();
  var url = "/bogus";

  for(var i in projects) {
    var project = projects[i];
    if (project.name == wiki || project.repo.search(wiki) > 0) {
      var url = "/snapshot/" + project.xlink;
      break;
    }
  }

  //console.log(">>> _listAll", wiki, projects, url);

  res.redirect(url);
}


function _getSnapshot(req, res) {
  var xid = req.params.xid;
  var cid = req.params.cid;
  var metadata = xidb.getMetadata(xid, cid);
  var assets = [];
  var changed = [];

  for(xid in metadata.assets) {
    var asset = metadata.assets[xid];
    var info = {
      'name': asset.name,
      'xlink': xidb.createLink(xid, asset.commit)
    };

    assets.push(info);

    if (asset.commit.indexOf(cid) == 0) {
      changed.push(info);
    }
  }

  assets.sort(function(a,b) {
    return a.name.localeCompare(b.name);
  });

  var treeView = new ui.TreeView(assets);

  res.render("snapshot", {
    title: "snapshot",
    commit: metadata.commit,
    tree: treeView.generateHtml(),
    assets: assets,
    changed: changed,
    nav: metadata.navigation
  });
}

function _getBranch(req, res) {
  var xid = req.params.xid;
  var cid = req.params.cid;
  var metadata = xidb.getMetadata(xid, cid);
  var assets = [];
  var changed = [];

  for(xid in metadata.assets) {
    var asset = metadata.assets[xid];
    var info = {
      'name': asset.name,
      'xlink': xidb.createLink(xid, asset.commit)
    };

    assets.push(info);

    if (asset.commit.indexOf(cid) == 0) {
      changed.push(info);
    }
  }

  assets.sort(function(a,b) {
    return a.name.localeCompare(b.name);
  });

  res.render("branch", {
    title: "branch",
    commit: metadata.commit,
    assets: assets,
    changed: changed,
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

  xidb.addComment(req.user, xlink, req.body.comment, function(err, link) {
    if (err) {
      console.log(err);
    }
    res.redirect(req.headers.referer + "#addComment");
  });
}

function _newVote(req, res) {
  var xid = req.params.xid;
  var cid = req.params.cid;
  var xlink = xidb.createLink(xid, cid);

  xidb.addVote(req.user, xlink, req.body, function(err, link) {
    if (err) {
      console.log(err);
    }
    res.redirect(req.headers.referer + "#addVote");
  });
}

function _getCompare(req, res) {

  var file = req.params.page;
  var page = file.substring(0, file.length-3);
  var revisions = req.params.revisions;

  xidb.getDiff(file, revisions, function(err, diff) {

    if (!err) {

      console.log(">>> diff", diff, "<<<");

      var lines = [];
      diff.split("\n").slice(4).forEach(function(line) {

        if (line.slice(0,1) != '\\') {
          lines.push({
            text: line,
            ldln: leftDiffLineNumber(0, line),
            rdln: rightDiffLineNumber(0, line),
            className: lineClass(line)
          });
        }
      });

      var revs = req.params.revisions.split("..");
      res.render('diff', {
        page: page,
	wiki: 'wiki',
        lines: lines,
        title: 'Revisions compare',
        revs: revs
      });

    }
    else {
      res.locals.title = "404 - Not found";
      res.statusCode = 404;
      res.render('404.jade');
      return;
    }
  });

  var ldln = 0,
      cdln;

  function leftDiffLineNumber(id, line) {

    var li;

    switch(true) {

      case line.slice(0,2) == '@@':
        li = line.match(/\-(\d+)/)[1];
        ldln = parseInt(li, 10);
        cdln = ldln;
        return '...';

      case line.slice(0,1) == '+':
        return "";

      case line.slice(0,1) == '-':
      default:
        ldln++;
        cdln = ldln - 1;
        return cdln;
    }
  }

  var rdln = 0;
  function rightDiffLineNumber(id, line) {

    var ri;

    switch(true) {

      case line.slice(0,2) == '@@':
        ri = line.match(/\+(\d+)/)[1];
        rdln = parseInt(ri, 10);
        cdln = rdln;
        return '...';

      case line.slice(0,1) == '-':
        return ' ';

      case line.slice(0,1) == '+':
      default:
        rdln += 1;
        cdln = rdln - 1;
        return cdln;
    }
  }

  function lineClass(line) {
    if (line.slice(0,2) === '@@') {
      return "gc";
    }
    if (line.slice(0,1) === '-') {
      return "gd";
    }
    if (line.slice(0,1) === '+') {
      return "gi";
    }
  }
}

module.exports = router;
