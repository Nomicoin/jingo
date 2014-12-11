var router = require("express").Router(),
    tools  = require("../lib/tools"),
    models = require("../lib/models"),
    app    = require("../lib/app").getInstance(),
    Feed   = require("feed");

models.use(Git);

router.get("/rss", _getRSS);
//server.use(express.basicAuth('test','testpass'));

function _getRSS(req, res) {
  var items = [];
  var pagen = 0 | req.query.page;
  var pages = new models.Pages();
  var appconfig = app.locals.config.get();

  var feed = new Feed({
          title: appconfig.application.title,
          description: 'RSS Feed',
          link: 'http://' + req.headers['host'] + req.url
  });

  pages.fetch(pagen,100).then(function() {
    pages.models.forEach(function(page) {
      if (!page.error) {
        items.push({
          page: page, 
          hashes: page.hashes.length == 2 ? page.hashes.join("..") : ""
        });
      }
    });
    res.writeHead(200, { 'Content-Type': 'text/plain' });
   
   items.forEach (function(item){
     feed.addItem({
       title: item.page.title + ' was updated by ' + item.page.metadata.author,
       link: 'http://' + req.headers['host'] + item.page.urlForShow(),
       content: 'Compare changes: http://' + req.headers['host'] + item.page.urlForCompare() + "/" + item.hashes,
       description: 'Last updated by ' + item.page.metadata.author,
       date: new Date(item.page.metadata.date),
       author: [
         {
           name: item.page.metadata.author
         }
       ]
     });
   });

   res.write (feed.render('rss-2.0')); 
   res.end();

  }).catch(function(ex) {
    console.log(ex);
  });
}

module.exports = router;
