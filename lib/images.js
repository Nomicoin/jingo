
// the middleware function
module.exports = function() {
    
  return function(req, res, next) {
    console.log('');
    console.log('>>> images middleware ' + req.path);

    if (req.path.match(/png$/)) {
      console.log('>>> png detected');
      res.end('png detected');
    }
    else {
      next();
    } 
  }
};

