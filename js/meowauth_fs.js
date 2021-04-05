/*
 *
 * To the extent possible under law, the person who associated CC0 with
 * this source code has waived all copyright and related or neighboring rights
 * to this source code.
 *
 * You should have received a copy of the CC0 legalcode along with this
 * work.  If not, see <http://creativecommons.org/publicdomain/zero/1.0/>.
 *
*/

// beginnings of site authorization for MeowCAD
// NOT FUNCTIONING / IN DEVELOPMENT
//
//
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

    var sha512 = crypto.createHash('sha512');
    var sessHash = sha512.update( userId + sessionId ).digest('hex');

    // create user, portoflio, project with a single sch and brd
    //   create the sch meta data, the current snapshot and current (base) index
    //   create the brd meta data, the current snapshot and current (base) index
    //   create session and add it to the pool
    // 

    var projName = randomName(json_words.word, 3) ;

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

    m.db.sadd( "projectpool", projId );

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


    m.db.hmset( "session:" + sessHash, 
        { id : sessHash, 
          userId : userId, 
          active : 1 
        });
    m.db.sadd( "sesspool", sessHash );

    console.log("anonymous userId: " + userId + ", sessionId: " + sessionId + ", sessHash: " + sessHash );
    console.log("  projectId: " + projId  );

    m.socket.emit("anonymouscreate", { 
      type:"response", 
      status:"success", 
      message:"anonymous user created", 
      userId: userId, 
      sessionId: sessionId,
      projectId: projId
    });
  }

};







