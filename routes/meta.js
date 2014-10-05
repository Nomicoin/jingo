var router = require("express").Router(),
renderer = require('../lib/renderer'),
fs = require("fs"),
models = require("../lib/models");

models.use(Git);

var files = [];

function initFiles() {
  Git.ls("*", function(err, list) {

    console.log("\n\n>>>meta " + list.length + "\n\n");

    for(var i = 0; i < list.length; i++) {
      files.push(list[i]);
      console.log(i, list[i]);
    } 
  });
}

initFiles();

router.get("/meta", _getMeta);

function _getMeta(req, res) {

  res.render("meta", {
    title: "meta",
    files: files
  });
}

module.exports = router;
