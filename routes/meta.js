var router = require("express").Router(),
    renderer = require('../lib/renderer'),
    fs = require("fs"),
    models = require("../lib/models");

models.use(Git);

router.get("/meta", _getMeta);

function _getMeta(req, res) {

  var page = "#meta\n";

  Git.ls("*", function(err, list) {

      console.log("\n\n>>>meta " + list.length + "\n\n");

     page += list.length + " files found\n";

      for(var i = 0; i < list.length; i++) {
          var file = list[i];
	  console.log(i, file);
	  page += "* [" + file + "](/meta/" + file + ")\n";
      } 

    console.log(page);

    res.render("minimal", {
      title: "meta",
      content: renderer.render(page)
    });
 });
}

module.exports = router;
