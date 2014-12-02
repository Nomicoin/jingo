var router = require("express").Router(),
    app    = require("../lib/app").getInstance(),
    renderer = require("../lib/renderer"),
    xmlrpc = require("xmlrpc"),
    fs = require("fs");
    
require("shelljs/global");

router.get("/admin", _getAdmin);
router.post("/admin", _getAdminData);

function _dummystuff(req, res) {
  if (!which("git")) {
    status = "Sorry, this script requires git";
  }

  exec('ls -la /home/v', {silent:true}, function(code, output) {
    console.log('Exit code:', code);
    console.log('Program output:', output);
  });
  
  var results = {command:res.locals.command, 
                  result:exec(res.locals.command, {silent:true}).output};

  res.render("admin", {
    status: status,
    command: res.locals.command,
    results: results
  });
}

function _getAdmin(req, res) {

  // Allow suggested commands in query string
  if (req.query.command) res.locals.command = req.query.command.trim();

  res.render("admin", {
    status: "Select a command from the list below: ",
    command: res.locals.command,
    results: ""
  });

}

function _getAdminData(req, res) {

  var bmParams = {
        host: app.locals.config.get("bitmessage").bmServer,
        port: app.locals.config.get("bitmessage").bmPort,
        path: app.locals.config.get("bitmessage").bmPath,
        basic_auth: {
          user: app.locals.config.get("bitmessage").bmUser,
          pass: app.locals.config.get("bitmessage").bmPassword
        }
  };
  var bitmessage = xmlrpc.createClient(bmParams);
  var status = "Sending from: " + app.locals.config.get("bitmessage").bmAddress;
  var publicGuildName = app.locals.config.get("application").publicGuildName;
      publicGuildName = new Buffer(publicGuildName).toString('base64');
  var bmAnnounce = app.locals.config.get("bitmessage").bmAnnounce;
      bmAnnounce = bmAnnounce.substr(3, bmAnnounce.length);
  var bmAddress = app.locals.config.get("bitmessage").bmAddress;
      bmAddress = bmAddress.substr(3, bmAddress.length);
  var userMessage = ""; if (req.body.message) userMessage = req.body.message.trim();
      userMessage = new Buffer(userMessage).toString('base64');
  var userCommand = ""; if (req.body.command) userCommand = req.body.command.trim();

  // Run command and render results
  switch (userCommand) {
  case ("list"):
    bitmessage.methodCall("listAddresses2","", function(error, value) {
      if (error) status = error;
      res.render("admin", {
                 status: status, 
                 command: userCommand, 
                 results: value});
    });
    break;
  case ("subs"):
    bitmessage.methodCall("listSubscriptions","", function(error, value) {
      if (error) status = error;
      res.render("admin", {
                 status: status, 
                 command: userCommand, 
                 results: value});
    });
    break;
    case ("all"):
      bitmessage.methodCall("getAllInboxMessages","", function(error, value) {
        if (error) status = error;
        res.render("admin", {
                   status: status,
                   command: userCommand,
                   results: value});
  });
  break;
  case ("send"):
    bitmessage.methodCall("sendMessage", [bmAnnounce, bmAddress, publicGuildName, userMessage], function(error, value) {
      if (error) status = error;
      res.render("admin", {
                 status: status, 
                 command: userCommand, 
                 results: value});
    });
    break;
  default:
    res.render("admin", {
               status: "Unrecognized command", 
               command: userCommand, 
               results: ""});
    break;
  }
}

module.exports = router;
