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

function fSessionGet( m )
{
  var db = m.db;
  var userId = m.data.userId;
  var sessionId = m.data.sessionId;

  //console.log(userId);
  //console.log(sessionId);

  var sha512 = crypto.createHash('sha512');
  var sessHash = sha512.update( userId + sessionId ).digest('hex');

  return function( callback ) { db.hgetall( "session:" + sessHash, callback ); };
}

function fValidateSession( m )
{
  var msgParent = m.messageParent;
  var db = m.db;
  var socket = m.socket;
  var userId = m.data.userId;

  return function( d, callback ){

    if (!d)
    {
      socket.emit( msgParent, { type:"response", status: "error", message: "authentication faliure" } );
      return;
    }

    dbUserId = d.userId;
    if (dbUserId != userId )
    {
      socket.emit( msgParent, { type:"response", status: "error", message: "authentication faliure" } );
      return;
    }

    callback(null, d);
  };
}

function fValidateItem( m )
{
  var msgParent = m.messageParent;
  var db = m.db;
  var socket = m.socket;
  var userId = m.data.userId;

  return function( d, callback )
  {
    if (!d)
    {
      socket.emit( msgParent, { type:"response", status: "error", message: "invalid schematic (1)" } );
      return;
    }

    console.log(d);


    console.log("userId: " + userId + " dbUserId: " + d.userId );

    if (d.userId != userId)
    {
      socket.emit( msgParent, { type:"response", status: "error", message: "invalid schematic (2)" } );
      return;
    }

    console.log("active? " + d.active);

    if (d.active != 1)
    {
      socket.emit( msgParent, { type:"response", status: "error", message: "invalid schematic (3)" } );
      return;
    }

    callback(null, d);
  }
}

function inputCheck( m )
{
  var userId = m.data.userId;
  var sessionId = m.data.sessionId;
  var msgParent = m.messageParent;

  if ( (typeof userId === 'undefined') ||
       (typeof sessionId === 'undefined') )
  {
    socket.emit(msgParent,  { 
      type: "response", 
      status: "error", 
      message : "userId, sessionId undefined" });
    return 0;
  }
  return 1;
}

function inputSchCheck( m )
{
  var userId = m.data.userId;
  var sessionId = m.data.sessionId;
  var schematicId = m.data.schematicId;
  var msgParent = m.messageParent;

  if ( (typeof userId === 'undefined') ||
       (typeof sessionId === 'undefined') ||
       (typeof schematicId === 'undefined')  )
  {
    m.socket.emit(msgParent,  { 
      type: "response", 
      status: "error", 
      message : "userId, sessionId or schematicId undefined" });
    return 0;
  }
  return 1;
}

function inputBrdCheck( m )
{
  var userId = m.data.userId;
  var sessionId = m.data.sessionId;
  var boardId = m.data.boardId;
  var socket = m.socket;
  var msgParent = m.messageParent;

  if ( (typeof userId === 'undefined') ||
       (typeof sessionId === 'undefined') ||
       (typeof boardId === 'undefined')  )
  {
    socket.emit( msgParent , { 
      type: "response", 
      status: "error", 
      message : "userId, sessionId or boardId undefined" });
    return 0;
  }
  return 1;
}

function _checkDBVal( userData, dbData, errorMessage)
{
  if (!dbData)
  {
    userData.socket.emit(userData.messageParent, { type:"response", status:"error", message: errorMessage});
    return 0;
  }
  return 1;
}

module.exports = {

  s4 : s4,
  guid : guid,

  // Authenticate the user and make sure the schematic exists
  //
  schAuth: function( m ) {
    console.log("meowproject schauth");

    m.messageParent = "schauth";

    if (!inputSchCheck( m ))
      return;

    async.waterfall([
      fSessionGet( m ),
      fValidateSession( m ),
      function(d, callback) {

        console.log("trying to fetch schematic: " + m.data.schematicId );

        m.db.hgetall( "sch:" + m.data.schematicId, callback );
      },
      fValidateItem( m ),
      function( d, callback )
      {

        m.transportData = { sch : d };

        m.db.hgetall( "project:" + d.projectId, callback );
      },
      fValidateItem( m ),
      function( d, callback )
      {
        console.log("ok!");


        console.log(d);

        m.socket.emit("schauth", 
          { type:"response", 
            status:"success", 
            message:"ok!", 
            ind: m.transportData.sch.ind, 
            schematicId: m.transportData.sch.id , 
            schematicName : m.transportData.sch.name  ,
            projectId : d.id,
            projectName : d.name
            //ind: d.ind, 
            //schematicId: d.id , 
            //schematicName : d.name  
          });
      }
      ],
      function( err, result) {
        console.log("schauth error");
        console.log(err);
        console.log(result);
      });
  },

  // Authenticate the user and make sure the schematic exists
  //
  schSnapshot : function( m ) {
    console.log("meowproject schsnapshot");

    m.messageParent = "schsnapshot";

    if (!inputSchCheck( m ))
      return;

    async.waterfall([
      fSessionGet( m ),
      fValidateSession( m ),
      function(d, callback) {

        console.log("trying to fetch schematic: " + m.data.schematicId );

        m.db.hgetall( "sch:" + m.data.schematicId , callback );
      },
      fValidateItem( m ),
      function( d, callback )
      {
        m.db.hgetall( "sch:" + m.data.schematicId + ":snapshot" , callback );
      },
      function( d, callback )
      {

        console.log("ok!");

        m.socket.emit("schsnapshot", { type:"response", status:"success", message:"ok!", data: d.data });
      }
      ],
      function( err, result) {
        console.log("schsnapshot error");
        console.log(err);
        console.log(result);
      });
  },

  // Authenticate the user and make sure the schematic exists
  //
  brdAuth : function( m ) {
    console.log("meowproject brdauth");

    m.messageParent = "brdauth";

    if (!inputBrdCheck( m ))
      return;

    async.waterfall([
      fSessionGet( m ),
      fValidateSession( m ),
      function(d, callback) {

        m.db.hgetall( "brd:" + m.data.boardId, callback );
      },
      fValidateItem( m ),
      function( d, callback )
      {
        m.socket.emit("brdauth", { type:"response", status:"success", message:"ok!" });
      }
      ],
      function( err, result) {
        console.log("brdauth error");
        console.log(err);
        console.log(result);
      });
  },

  newProject : function( m ) {
    console.log("meowproject newproject");
    m.messageParent = "newproject";

    var projName = 
      ( (typeof m.data.projectName === 'undefined') ? randomName(json_words.word, 2) : m.data.projectName );
    var schName =
      ( (typeof m.data.schematicName === 'undefined') ? randomName(json_words.word, 3) : m.data.schematicName );
    var brdName =
      ( (typeof m.data.boardName === 'undefined') ? randomName(json_words.word, 3) : m.data.boardName );

    if (!inputCheck( m )) 
      return;

    async.waterfall([
      fSessionGet( m ),
      fValidateSession( m ),
      function(d, callback) {

        var userId = m.data.userId;

        var projId = guid();
        var schId = guid();
        var brdId = guid();

        console.log( "userId: " + String(userId) + ", projId: " + projId);

        m.db.rpush( "olio:" + String(userId), projId );
        m.db.hmset( "project:" + projId, 
          { id: projId, 
            userId : userId, 
            name: projName,
            sch: schId, 
            brd: brdId, 
            permission:"user", 
            active : "1" });


        m.db.hmset( "sch:" + schId, 
            { id : schId, 
              userId : userId, 
              projectId : projId, 
              name: schName,
              active : "1",
              ind : "0" });

        m.db.hmset( "sch:" + schId + ":0", { data : "{ \"element\" : [] }" });
        m.db.hmset( "sch:" + schId + ":snapshot", { data : "{ \"element\" :[] }" });

        m.db.hmset( "brd:" + brdId, 
            { id : brdId, 
              userId : userId, 
              projectId : projId, 
              name: brdName,
              active : "1",
              ind : "0" });
        m.db.hmset( "brd:" + brdId + ":0", { data : "{ \"element\" :[] }" });
        m.db.hmset( "brd:" + brdId + ":snapshot", { data : "{ \"element\" :[] }" });


        console.log("newproject created");


        m.socket.emit("newproject", {
                type:"response",
                status:"success",
                message:"new project created",
                projId: projId,
                schId: schId,
                brdId: brdId 
        });

        console.log("finishing");
      }
      ],
      function( err, result) {
        console.log("newproject error");
        console.log(err);
        console.log(result);
      });
  },


  // From client to server, update incrementally
  //
  schFullPush : function( m ) {
    console.log("meowproject schfullpush");

    m.messageParent = "schfullpush";

    if (!inputSchCheck( m ))
      return;

    async.waterfall([
      fSessionGet( m ),
      fValidateSession( m ),
      function(d, callback) {
        m.db.hgetall( "sch:" + m.data.schematicId, callback );
      },
      fValidateItem( m ),
      function( d, callback )
      {
        console.log("cp1, schematicId: " + m.data.schematicId);

        var key = "sch:" + m.data.schematicId + ":snapshot";
        //var val = { data: JSON.stringify(m.data.json_sch) };
        var val = { data: m.data.json_sch };

        console.log(key);
        console.log(val);

        //m.db.hmset( key, "data", JSON.stringify(m.data.json_sch) );
        m.db.hset( key, "data", m.data.json_sch );

        m.db.hgetall( "sch:" + m.data.schematicId, callback)
      },
      function( d, callback )
      {
        if (!d)
        {
          m.socket.emti("schfullpush", 
              { type:"response", 
                status:"error", 
                message:"couldn't get schematic:" + m.data.schematicId });
          return;
        }
        var k = parseInt(d.ind);
        k++;

        console.log("cp2");

        var key = "sch:" + m.data.schematicId + ":" + k;
        var val = 

        //m.db.hmset( "sch:" + m.data.schematicId + ":" + k, { data: JSON.stringify(m.data.json_sch) });
        //m.db.hmset( key , "data", JSON.stringify(m.data.json_sch) );
        m.db.hmset( key , "data", m.data.json_sch );

        key = "sch:" + m.data.schematicId;
        m.db.hmset( key , "ind", k );


        m.socket.emit("schfullpush", 
            { type:"response", 
              status:"success", 
              message:"ok!", 
              ind: k, 
              schematicId : m.data.schematicId  });
      }

      ],
      function( err, result) {
        console.log("schfullpush error");
        console.log(err);
        console.log(result);
      });
  },

  // From client to server, update incrementally
  //
  brdFullPush : function( m ) {
    console.log("meowproject brdfullpush");

    m.messageParent = "brdfullpush";

    if (!inputSchCheck( m ))
      return;

    async.waterfall([
      fSessionGet( m ),
      fValidateSession( m ),
      function(d, callback) {
        m.db.hgetall( "brd:" + m.data.boardId, callback );
      },
      fValidateItem( m ),
      function( d, callback )
      {
        //m.db.hmset("brd:" + m.data.boardId + ":snapshot", { data: JSON.stringify(m.data.json_brd) });
        m.db.hmset("brd:" + m.data.boardId + ":snapshot", { data: m.data.json_brd });
        m.db.hgetall( "brd:" + m.data.boardId, callback)
      },
      function( d, callback )
      {
        if (!d)
        {
          m.socket.emti("brdfullpush", 
            { type:"response", 
              status:"error", 
              message:"couldn't get schematic:" + m.data.boardId });
          return;
        }
        var k = parseInt(d.ind);
        k++;
        //m.db.hmset( "brd:" + m.data.boardId + ":" + k, { data: JSON.stringify(m.data.json_brd) });
        m.db.hmset( "brd:" + m.data.boardId + ":" + k, { data: m.data.json_brd });
        m.socket.emit("brdfullpush", { type:"response", status:"success", message:"ok!" });
      }

      ],
      function( err, result) {
        console.log("brdfullpush error");
        console.log(err);
        console.log(result);
      });
  }
  
  /*
  ,

  // From client to server, update incrementally
  //
  schUpdate : function( m ) {
    console.log("meowsch update");

    m.messageParent = "schupdate";

    if (!inputCheck( m ))
      return;

    async.waterfall([
      fSessionGet( m.db, sessionId ),
      fValidateSession( msgParent, m.db, m.socket, userId ),

      function( d, callback )
      {
      }

      ],
      function( err, result) {
        console.log("schupdate error");
        console.log(err);
        console.log(result);
      });
  },

  // Get current snapshot from server to client
  //
  get : function( m ) {
    console.log("meowsch get");

    m.messageParent = "schget";

    if (!inputCheck(m)) return;
    async.waterfall([
      fSessionGet( m.db, sessionId ),
      fValidateSession( msgParent, m.db, m.socket, userId ),

      function( d, callback )
      {
        m.db.hgetall( "sch:" + m.data.schematicId, callback );
      },
      function(d, callback)
      {
        if (!_checkBDVal(m, d, "no schematic"))
          return;
        m.db.hgetall( "sch:" + m.data.schematicId + ":snapshot", callback );
      },

      function(d, callback)
      {
        if (!_checkBDVal(m, d, "no snapshot"))
          return;
        m.socket.emit("schupdate", { type:"response", status:"success", message:"success", data: d.data });
      }

      ],
      function( err, result) {
        console.log("schupdate error");
        console.log(err);
        console.log(result);
      });
  },

  // Push from client to server, 
  // send (from client to server) current snapshot
  //
  put: function( m ) {
    console.log("meowsch push");

    m.messageParent = "schput";

    if (!inputCheck(m)) return;

    async.waterfall([
      fSessionGet( m.db, sessionId ),
      fValidateSession( msgParent, m.db, m.socket, userId ),
      function( d, callback )
      {
        m.db.hmset( "sch:" + m.data.schematicId + ":snapshot", { data: m.data.schematicData });
        m.socket.emit("schput", { type:"response", status:"error", message:"ok" });
      }
      ],
      function( err, result) {
        console.log("schupdate error");
        console.log(err);
        console.log(result);
      });

  },

  // Pull from server to client,
  pull : function( m ) {
    console.log("meowsch pull");

    m.messageParent = "schpush";

    if (!inputCheck(m)) return;

    async.waterfall([
      fSessionGet( m.db, sessionId ),
      fValidateSession( msgParent, m.db, m.socket, userId ),
      function( d, callback )
      {

      }
      ],
      function( err, result) {
        console.log("schupdate error");
        console.log(err);
        console.log(result);
      });

  }
  */

};







