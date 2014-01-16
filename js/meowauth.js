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

  meow : function( m ) {
    console.log("meow request (authenticated meow)");

    var socket = m.socket;
    var db = m.db;

    var sessionId = m.data.sessionId;
    var userId = m.data.userId;

    if ( ( typeof sessionId === 'undefined' ) ||
         ( typeof userId === 'undefined' ) )
    {
      console.log("cp0");
      socket.emit("meow", { type: "response", status: "error", message: "no sessionId or userId" } );
      return;
    }

    console.log("starting waterfall");

    async.waterfall([
        function(callback)
        {
          var sha512 = crypto.createHash('sha512');
          var sessHash = sha512.update( userId + sessionId ).digest('hex');

          console.log("sessHash: " + sessHash);

          db.hgetall( "session:" + sessHash , callback );
        },
        function(d, callback)
        {

          console.log("got:");
          console.log(d);

          if ( (!d)  || (d.active != "1") )
          {
            console.log("cp1");
            socket.emit("meow", { type: "response", status: "error", message: "authentication failure" } );
            return;
          }

          console.log("emitting mew");

          socket.emit("mew", { type: "response", status: "success", message: "mew" } );

        }
        ],
        function(err, result)
        {
          console.log("meow (auth) error:");
          console.log(err);
          console.log(result);
        }
    );
  },
  
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

          setTimeout(
            function() {
              socket.emit("auth", { type:"response", status: "error", message:"authentication failed" });
            },
            1000
            );
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
          setTimeout(
              function() {
                socket.emit("auth", { type:"response", status: "error", message:"authentication failed" }) ;
              },
            1000
            );
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
          setTimeout(
            function() {
              socket.emit("auth", { type:"response", status: "error", message:"authentication failed" }) ;
            },
            1000
            );
          return;
        }
      }
    ], function(err, result) {
      console.log("got err:");
      console.log(err);
      console.log(result);
    });

  },

  anonymous : function( m )
  {
    console.log("creating anonymous user and anonymous board and schematic");

    var userId = guid();
    var dummyPassHash = guid();
    var sessionId = guid();
    var projId = guid();
    var schId = guid();
    var brdId = guid();

    var sha512 = crypto.createHash('sha512');
    var sessHash = sha512.update( userId + sessionId ).digest('hex');

    // create user, portoflio, project with a single sch and brd
    //   create the sch meta data, the current snapshot and current (base) index
    //   create the brd meta data, the current snapshot and current (base) index
    //   create session and add it to the pool
    // 

    m.db.hmset( "user:" + userId, { id : userId, userName: "", passwordHash: dummyPassHash, type : "anonymous" });

    m.db.rpush( "olio:" + userId, projId );
    m.db.hmset( "project:" + projId, { id: projId, userId : userId, name:"", sch: schId, brd: brdId, permission:"user" });

    m.db.hmset( "sch:" + schId, { id : schId, userId : userId, projectId : projId, name: "", ind : 0 });
    m.db.hmset( "sch:" + schId + ":0", { data : "{ element:[] }" });
    m.db.hmset( "sch:" + schId + ":snapshot", { data : "{ element:[] }" });

    m.db.hmset( "brd:" + brdId, { id : brdId, userId : userId, projectId : projId, name: "", ind : 0 });
    m.db.hmset( "brd:" + brdId + ":0", { data : "{ element:[] }" });
    m.db.hmset( "brd:" + brdId + ":snapshot", { data : "{ element:[] }" });

    m.db.hmset( "session:" + sessHash, { id : sessHash, userId : userId, active : 1 } );
    m.db.sadd( "sesspool", sessHash );

    console.log("anonymous userId: " + userId + ", sessionId: " + sessionId + ", sessHash: " + sessHash );
    console.log("  projectId: " + projId + ", schId: " + schId + ", brdId:" + brdId );

    m.socket.emit("anonymous", { 
      type:"response", 
      status:"success", 
      message:"anonymous user created", 
      userId: userId, 
      sessionId: sessionId,
      projId: projId,
      schId: schId,
      brdId: brdId });
  }

};







