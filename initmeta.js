var Promise = require('bluebird');
var git = Promise.promisifyAll(require('./lib/gitmech'));

git.setup('', '/home/david/dev/Meridion.wiki', '', '', function(err, version) {

  if (err) {
    console.log(err);
    process.exit(-1);
  }

  git.log(".", "HEAD", 10, function(err, log) {
    console.log(log);
  });

  // git.lsRev("*", "accffdc", function(err, list) {

  //   console.log(list.length + " files found\n\n");

  //   for(var i = 0; i < list.length; i++) {
  //     var file = list[i];
  //     console.log(file);
  //   }
  // });

});

