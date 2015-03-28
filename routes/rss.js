var router = require("express").Router(),
app    = require("../lib/app").getInstance(),
xidb   = require("../lib/xidb");
Feed   = require("feed");

router.get("/rss", _getRSS);

function _getRSS(req, res) {
  var appconfig = app.locals.config.get();
  var feed = new Feed({
    title: appconfig.application.title,
    description: 'RSS Feed',
    link: 'http://' + req.headers['host'] + req.url
  });

  var projects = xidb.getProjectList();
  var project = projects[appconfig.application.title];
  var xid = project.xid.slice(0, 8);

  xidb.getLog(function(err, items) {

    items.forEach (function(item){
      var xlink = xid + '/' + item.cid.slice(0,8);
      var url = 'http://' + req.headers['host'] + '/branch/' + xlink;

      feed.addItem({
	title: item.subject,
	guid: item.cid,
	link: url,
	content: 'See changes: ' + url,
	description: 'Last updated by ' + item.name,
	date: new Date(item.date),
	author: [
          {
            name: item.name
          }
	]
      });
    });

    res.write (feed.render('rss-2.0')); 
    res.end();
  });
}

module.exports = router;
