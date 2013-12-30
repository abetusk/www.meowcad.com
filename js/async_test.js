async = require("async");

var call_order = [];
async.waterfall([
  function(callback){
    call_order.push("fn1");
    callback(null, 'one', 'two');
  },
  function(arg1, arg2, callback){
    call_order.push(arg1);
    call_order.push(arg2);
    callback(null, 'three');
  },
  function(arg1, callback){
    // arg1 now equals 'three'
    call_order.push(arg1);
    callback(null, 'done');
  }
], function (err, result) {
  // result now equals 'done'    

  console.log(call_order);
});


console.log("hello");


