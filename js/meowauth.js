var crypto = require('crypto');
var async = require("async");

function authResponse( m )
{
  console.log("auth response (" + m.uid + ")" );
  m.socket.emit("auth", { type:"response", status:"success", sesstok : m.uid } );
}

function s4() {
    return Math.floor((1 + Math.random()) * 0x10000)
      .toString(16)
      .substring(1);
}

function guid() {
    return s4() + s4() + '-' +
           s4() + '-' +
           s4() + '-' +
           s4() + '-' + s4() + s4() + s4();
}


function createAuthSession( m )
{

  var userid = m.userId;
  var socket = m.socket;
  var db = m.db;

  console.log("createAuthSession");
  console.log(userid);

  var sessionId = guid();

  var sha512 = crypto.createHash('sha512');
  var hashSessionId = sha512.update( userid + sessionId ).digest('hex');

  db.sadd( "sesspool", hashSessionId );
  db.hmset( "session:" + hashSessionId , { id : hashSessionId, userId : userid , active : 1 });
  socket.emit("auth", { type:"response", status:"success", sessionId: sessionId, userId: userid });

}

function emitAuthError( socket )
{
  socket.emit("auth", { type:"response", status:"error",  message:"authentication failed" }) ;
}

module.exports = {

  s4 : s4,
  guid : guid,
  
  authRequest : function( m ) {
    console.log("auth request (" + m.transactionId + ")");

    var uname = m.data.username;
    var pword = m.data.password;
    var socket = m.socket;
    var db = m.db;

    console.log(uname);
    console.log(pword);

    async.waterfall([
      function(callback)        // get userid
      {
        db.hgetall( "username:" + uname, callback );
      },
      function(d, callback)     // 
      {

        if (!d)
        {
          console.log("fail (1)!");
          socket.emit("auth", { type:"response", status: "error", message:"authentication failed" }) ;
          return ;
        }

        console.log("got:");
        console.log(d);

        var userid = d.id;
        var username = d.userName;

        if (!userid) 
        {
          emitAuthError( socket );
          return;
        }

        db.hgetall( "user:" + userid, callback );
      },
      function(d, callback)
      {
        if (!d)
        {
          console.log("fail (2)!");
          socket.emit("auth", { type:"response", status: "error", message:"authentication failed" }) ;
          return ;
        }


        var userid = d.id;
        var username = d.userName;
        var passwordHash = d.passwordHash;

        console.log(passwordHash);

        var sessionId = guid();

        var sha512 = crypto.createHash('sha512');
        //sha512.update(sessionId);
        var testHashPass = sha512.update( userid + pword ).digest('hex');

        console.log(userid);
        console.log(pword);
        console.log(testHashPass);

        if ( testHashPass == passwordHash )
        {
          console.log("passed!");
          m.userId = userid;
          createAuthSession( m );
        }
        else 
        {
          console.log("fail!");
          socket.emit("auth", { type:"response", status: "error", message:"authentication failed" }) ;
          return;
        }
      }
    ], function(err, result) {
      console.log("got err:");
      console.log(err);
      console.log(result);
    });

  },

  bar : function() {
    console.log("bar");
  }

};







