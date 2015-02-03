var xidb = require('./xidb');
var renderer = require('./renderer');

var Asset = function(data, metadata) {
  this.data = data;
  this.metadata = metadata;
}

Asset.prototype.getView = function() {
  return "asset";
}

Asset.prototype.getEditor = function() {
  return "asset-edit";
}

Asset.prototype.wiki2html = function(text) {
  return renderer.render(text);
}

Asset.prototype.getXlink = function() {
  return this.metadata.base.xlink;
}

// ===================================

var Vote = function(data, metadata) {
  this.data = JSON.parse(data);
  this.metadata = metadata;
}

Vote.prototype.getView = function() {
  return "vote"; // TD: move to metadata
}

Vote.prototype.getAgent = function() {
  var agent = xidb.getMetadataFromLink(this.data.agent);
  //console.log(agent);
  return agent;
}

Vote.prototype.getRef = function() {
  var ref = xidb.getMetadataFromLink(this.data.ref);
  //console.log(ref);
  return ref;
}

// ===================================

function _getXlinkForPage(page) {
  var wiki = 'wiki';
  var repoDir = xidb.getRepoGitDir(wiki);
  var head = xidb.getHeadCommit(repoDir);
  var cid = head.slice(0,8);
  var file = page.replace(/ /g, "-") + '.md';
  var snapshot = xidb.getWikiSnapshot(wiki, cid);
  var xlink = xidb.getMetalink(snapshot, file, true);

  if (xlink == null) {
    // check for legacy versioned URL
    cid = path.basename(page);
    snapshot = xidb.getWikiSnapshot(wiki, cid);
    page = path.dirname(page);
    file = page.replace(/ /g, "-") + '.md';
    xlink = xidb.getMetalink(snapshot, file, true);
  }

  return xlink;
}

var Proposal = function(data, metadata) {
  this.data = JSON.parse(data);
  this.metadata = metadata;

  var page = this.data.title.slice(2,-2);
  var xlink = _getXlinkForPage(page);

  console.log(">>> proposal ctor", this.data.title, page, xlink);

  this.pageMetadata = xidb.getMetadataFromLink(xlink);

  console.log(">>> proposal ctor", this.pageMetadata);
}

Proposal.prototype = Object.create(Asset.prototype);

Proposal.prototype.getView = function() {
  return "proposal"; // TD: move to metadata
}

Proposal.prototype.getEditor = function() {
  return "proposal-edit"; // TD: move to metadata
}

Proposal.prototype.getTitle = function() {
  return this.wiki2html(this.data.title);
}

Proposal.prototype.getProposalId = function() {
  return this.data.propid;
}

Proposal.prototype.getProposalTypes = function() {
  return ['rule', 'resolution', 'definition', 'goal', 'amendment', 'repeal'];
}

Proposal.prototype.getProposalType = function() {
  return this.data.type;
}

Proposal.prototype.getProposalContent = function() {
  return this.pageMetadata.as.html;
}

Proposal.prototype.getStatuses = function() {
  return ['wip', 'voting', 'passed', 'rejected', 'withdrawn'];
}

Proposal.prototype.getStatus = function() {
  return this.data.status;
}

Proposal.prototype.getSponsors = function() {
  return this.wiki2html(this.data.sponsors.join('\n'));
}

Proposal.prototype.getRationale = function() {
  return this.wiki2html(this.data.rationale);
}

// ===================================

var Agent = function(data, metadata) {
  this.data = JSON.parse(data);
  this.metadata = metadata;
}

Agent.prototype = Object.create(Asset.prototype);

Agent.prototype.getView = function() {
  return "agent";
}

Agent.prototype.getComments = function() {
  try { 
    var comments = this.metadata.base.pubs.comment.map(function(xlink) {
      return xidb.getMetadataFromLink(xlink);
    });
    //console.log(comments);
    return comments;
  }
  catch (e) {
    return null;
  }
}

Agent.prototype.getVotes = function() {
  try {
    var votes = this.metadata.base.pubs.vote.map(function(xlink) {
      return xidb.getMetadataFromLink(xlink);
    });
    //console.log(votes);
    return votes;
  }
  catch (e) {
    return null;
  }
}

// ===================================

function createAsset(data, metadata) {
  var kind = metadata.base.kind;
  var asset;

  console.log(">>> createAsset", kind);

  switch(kind) {
    case 'Proposal':
    asset = new Proposal(data, metadata);
    break;

    case 'Agent':
    asset = new Agent(data, metadata);
    break;

    case 'Vote':
    asset = new Vote(data, metadata);
    break;

    default:
    asset = new Asset(data, metadata);
    break;
  }
  
  //console.log(">>> asset=", asset);

  return asset;
}

var assets = {
  Asset: Asset,
  Agent: Agent,
  createAsset: createAsset
};

module.exports = assets;
