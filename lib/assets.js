var Asset = function(data, metadata) {
  this.data = data;
  this.metadata = metadata;
}

Asset.prototype.getView = function() {
  return "asset";
}

var Agent = function(data, metadata) {
  this.data = JSON.parse(data);
  this.metadata = metadata;
}

Agent.prototype.getView = function() {
  return "agent";
}

Agent.prototype.getComments = function() {
  try {
    return this.metadata.base.pubs.comment;
  }
  catch (e) {
    return null;
  }
}

Agent.prototype.getVotes = function() {
  try {
    return this.metadata.base.pubs.vote;
  }
  catch (e) {
    return null;
  }
}

function createAsset(data, metadata) {
  var kind = metadata.base.kind;
  var asset;

  console.log(">>> createAsset", kind);

  switch(kind) {
    case 'Agent':
    asset = new Agent(data, metadata);
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
