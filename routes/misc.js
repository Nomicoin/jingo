var router = require("express").Router(),
    renderer = require('../lib/renderer'),
    fs = require("fs");

router.get("/misc/syntax-reference", _getSyntaxReference);
router.post("/misc/preview",         _postPreview);

function _getSyntaxReference(req, res) {
  res.render('syntax');
}

function _postPreview(req, res) {
  res.render('preview', {
    content: renderer.render(req.body.data)
  });
}

router.all('*', function(req, res) {
  res.locals.title = "404 - Not found";
  res.statusCode = 404;
  res.render('404.jade');
});

module.exports = router;
