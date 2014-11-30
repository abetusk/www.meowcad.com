var crypto = require('crypto');
var async = require("async");

var fs = require('fs');

var json_words = null;
var json_words_fn = "./american-english.json";

function randomName( word_list, n ) {
  var s = "";
  for (var i=0; i<n; i++)
  {
    var k = parseInt( Math.random() * word_list.length );
    if (i > 0)
      s += " ";
    s += word_list[k];
  }
  return s;
}

fs.readFile(json_words_fn, "utf8", function(err, data) {
  if (err) {
    console.log("got error: " + err);
    return;
  }

  json_words = JSON.parse(data);

  /*
  console.log("dictionary loaded");
  console.log("???");
  console.log(json_words.word[0]);
  console.log("??");
  console.log("here are some random names:");
  console.log( randomName(json_words.word, 2) );
  console.log( randomName(json_words.word, 2) );
  console.log( randomName(json_words.word, 3) );
  console.log( randomName(json_words.word, 3) );
  console.log( randomName(json_words.word, 3) );
  */

});


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
          //console.log(d);

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
        //console.log(d);

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

  anonymousCreate : function( m )
  {
    console.log("creating anonymous user and anonymous board and schematic");

    var userId = guid();
    var dummyPassHash = guid();
    var sessionId = guid();
    var projId = guid();
    //var schId = guid();
    //var brdId = guid();

    var sha512 = crypto.createHash('sha512');
    var sessHash = sha512.update( userId + sessionId ).digest('hex');

    // create user, portoflio, project with a single sch and brd
    //   create the sch meta data, the current snapshot and current (base) index
    //   create the brd meta data, the current snapshot and current (base) index
    //   create session and add it to the pool
    // 

    var projName = randomName(json_words.word, 3) ;
    //var schName  = randomName(json_words.word, 3) ;
    //var brdName  = randomName(json_words.word, 3) ;

    var blankSch = "{ \"element\":[], \"component_lib\":{}, \"net_pin_id_map\":{} }";
    var blankBrd = "{ \"element\":[], " + 
                    " \"equipot\" : [ { \"net_name\" : \"\", \"net_number\" : 0 }], " + 
                    " \"units\" : \"deci-mils\"  }";

    m.db.hmset( "user:" + userId, 
        { id : userId, 
          userName: "anonymous", 
          passwordHash: dummyPassHash, 
          type : "anonymous" ,
          active : "1"
        });

    m.db.sadd( "userpool", userId );

    var dt = new Date();
    var sec = dt.getTime();
    var dt_str = String(1900 + dt.getYear()) + "-" + 
                 String(1+dt.getMonth()) + "-" + 
                 String(dt.getDate()) + " " +
                 String(dt.getHours()) + ":" +
                 String(dt.getMinutes()) + ":" + 
                 String(dt.getSeconds()) ;
    m.db.rpush( "olio:" + userId, projId );
    m.db.hmset( "project:" + projId, 
        { id: projId, 
          userId : userId, 
          name: projName,

          stime : sec,
          timestamp : dt_str,
          
          permission:"user", 
          active:1 
        });

    m.db.hmset( "projectrecent:" + userId, { projectId: projId });


    m.db.hmset( "projectsnapshot:" + projId,
        { id : projId,
          json_sch : blankSch,
          json_brd : blankBrd 
        });

    var eventId = guid();

    var op = { type : "snapshot", source : "none", destination : "none" };
    op.action = "snapshot";
    op.data = { json_sch : blankSch, json_brd : blankBrd };
    var str_op = JSON.stringify( op );

    m.db.hmset( "projectop:" + projId + ":" + eventId,
        { id : eventId,
          data : str_op
        });

    m.db.rpush( "projectevent:" + projId, eventId );



    /*
    m.db.hmset( "sch:" + schId, 
        { id : schId, 
          userId : userId, 
          projectId : projId, 
          name: schName,
          ind : 0, 
          active:1 
        });
    m.db.hmset( "sch:" + schId + ":0", { data : blankSch });
    m.db.hmset( "sch:" + schId + ":snapshot", { data : blankSch });
    //m.db.hmset( "sch:" + schId + ":0", { data : "{ \"element\":[] }" });
    //m.db.hmset( "sch:" + schId + ":snapshot", { data : "{ \"element\":[] }" });
    */

    /*
    m.db.hmset( "brd:" + brdId, 
        { id : brdId, 
          userId : userId, 
          projectId : projId, 
          name: brdName,
          ind : 0, 
          active:1 
        });
    m.db.hmset( "brd:" + brdId + ":0", { data : blankBrd });
    m.db.hmset( "brd:" + brdId + ":snapshot", { data : blankBrd });
    //m.db.hmset( "brd:" + brdId + ":0", { data : "{ element:[] }" });
    //m.db.hmset( "brd:" + brdId + ":snapshot", { data : "{ element:[] }" });
    */

    m.db.hmset( "session:" + sessHash, 
        { id : sessHash, 
          userId : userId, 
          active : 1 
        });
    m.db.sadd( "sesspool", sessHash );

    /*
    m.db.hmset( "recentsession:" + userId,
        { schematicId : schId,
          boardId : brdId
        });
        */

    console.log("anonymous userId: " + userId + ", sessionId: " + sessionId + ", sessHash: " + sessHash );
    //console.log("  projectId: " + projId + ", schId: " + schId + ", brdId:" + brdId );
    console.log("  projectId: " + projId  );

    m.socket.emit("anonymouscreate", { 
      type:"response", 
      status:"success", 
      message:"anonymous user created", 
      userId: userId, 
      sessionId: sessionId,
      projectId: projId
      //,
      //schematicId: schId,
      //boardId: brdId 
    });
  }

};







