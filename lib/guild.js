var fs = require('fs');
var path = require('path');
var Configurable = require("./configurable");

var Guild = function () {
  Configurable.call(this);

  var config = this.getConfig().application;
  this.guildDir = config.guild;
  this.guildAgentsDir = path.join(config.guild, "agents/data/");
};

Guild.prototype = Object.create(Configurable.prototype);

Guild.prototype.getAgentsList = function() {
  var agents = [];
  var agentsDir = fs.readdirSync(this.guildAgentsDir);

  agentsDir.forEach(function(agentFile) {
     agents.push(agentFile.split('.')[0]);
  }); 
  return agents;
}

Guild.prototype.getAgent = function(agentId) {
  var agents = this.getAgentsList();

  for (var name in agents) {
    var agent = agents[name];
    if (agent == agentId) {
      var agentFile = this.guildAgentsDir + agentId + '.json';
      try {
        var agentInfo = JSON.parse(fs.readFileSync(agentFile, 'utf8'));
      } catch(err) {
        console.log ("Found agent " + agentId + ", but can't load agent profile. " + err);
        return null;
      }
    }
  }
  return agentInfo;
}

Guild.prototype.getAgentName = function(agentId) {
  var agent = this.getAgent(agentId);
  try { var agentName = agent.contact.name; }
  catch (err) { var agentName = null; }
  return agentName;
}

Guild.prototype.getAgenteMail = function(agentId) {
  var agent = this.getAgent(agentId);
  try { var agenteMail = agent.contact.email; }
  catch (err) { var agentMail = null; }
  return agenteMail;
}

Guild.prototype.getAgentRSSKey = function(agentId) {
  var agent = this.getAgent(agentId);
  try { var agentRSSKey = agent.contact.rsskey; }
  catch (err) { var agentRSSKey = null; } 
  return agentRSSKey;
}

Guild.prototype.getAgentBMAddress = function(agentId) {
  var agent = this.getAgent(agentId);
  try { var agentBMAddress = agent.contact.bitmessage; }
  catch (err) { var agentBMAddress = null; }
  return agentBMAddress;
}


module.exports = new Guild();
