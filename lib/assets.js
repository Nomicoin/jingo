var xidb = require('./xidb');

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
    console.log(comments);
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
    console.log(votes);
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
  
  console.log(">>> asset=", asset);

  return asset;
}

var assets = {
  Asset: Asset,
  Agent: Agent,
  createAsset: createAsset
};

module.exports = assets;
