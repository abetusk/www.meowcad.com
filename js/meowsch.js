var crypto = require('crypto');
var async = require("async");

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
  var sessionId = m.sessionId;
  return function( callback ) { db.hgetall( "session:" + sessionId, callback ); };
}

function fValidateSession( m )
{
  var msgParent = m.messageParent;
  var db = m.db;
  var socket = m.socket;
  var userId = m.userId;

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

    callback(d);
  };
}

function fValidateSchematic( m )
{
  var msgParent = m.messageParent;
  var db = m.db;
  var socket = m.socket;
  var userId = m.userId;


  return function( d, callback )
  {
    if (!d)
    {
      socket.emit( msgParent, { type:"response", status: "error", message: "invalid schematic" } );
      return;
    }

    if (d.userId != userId)
    {
      socket.emit( msgParent, { type:"response", status: "error", message: "invalid schematic" } );
      return;
    }

    callback(d);
  }
}

function inputCheck( m )
{
  var userId = m.data.userId;
  var sessionId = m.data.sessionId;
  var schematicId = m.data.schematicId;
  var socket = m.socket;

  if ( (typeof userId === 'undefined') ||
       (typeof sessionId === 'undefined') ||
       (typeof schematicId === 'undefined')  )
  {
    socket.emit("schupdate", { 
      type: "response", 
      status: "error", 
      message : "userId, sessionId or schematicId undefined" });
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
  auth : function( m ) {
    console.log("meowsch auth");

    m.messageParent = "schauth";

    if (!inputCheck( m ))
      return;

    async.waterfall([
      fSessionGet( m ),
      fValidateSession( m ),
      function(d, callback) {
        m.db.hgetall( "schematic:" + m.schematicId, fValidateSchematic );
      },
      fValidateSchematic( m ),
      function( d, callback )
      {
        m.scoket.emit("schauth", { type:"response", status:"success", message:"ok!" });
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
  newSchematic : function( m ) {
    console.log("meowsch new");
    m.messageParent = "schnew";
    if (!inputCheck( m )) return;
    async.waterfall([
      fSessionGet( m ),
      fValidateSession( m ),
      function(d, callback) {
        var schId = guid();
        m.db.hmset( "schematic:" + schId, { data : "{ element:[] }" } );
        m.db.hmset( "schematic:" + schId + ":snapshot", { data : "{ element:[] }" } );
        m.scoket.emit("schnew", { type:"response", status:"error", schematicId : schId, message:"new schematic created" });
      }
      ],
      function( err, result) {
        console.log("schauth error");
        console.log(err);
        console.log(result);
      });
  },

  // From client to server, update incrementally
  //
  fullPush : function( m ) {
    console.log("meowsch fullPush");

    m.messageParent = "schfullpush";

    if (!inputCheck( m ))
      return;

    async.waterfall([
      fSessionGet( m ),
      fValidateSession( m ),
      function(d, callback) {
        m.db.hgetall( "schematic:" + m.schematicId, fValidateSchematic );
      },
      fValidateSchematic( m ),
      function( d, callback )
      {
        m.db.hmset("schematic:" + m.schematicId + ":snapshot", { data: JSON.stringify(m.data.json_sch) });
        m.db.hgetall( "schematic:" + m.schematicId, callback)
      },
      function( d, callback )
      {
        if (!d)
        {
          m.socket.emti("schfullpush", {type:"response", status:"error", message:"couldn't get shcemtic:" + m.schematicId });
          return;
        }
        var k = parseInt(d.ind);
        k++;
        m.db.hmset( "schematic:" + m.schematicId + ":" + k, { data: JSON.stringify(m.data.json_sch) });
        m.scoket.emit("schfullpush", { type:"response", status:"success", message:"ok!" });
      }

      ],
      function( err, result) {
        console.log("schupdate error");
        console.log(err);
        console.log(result);
      });
  },

  // From client to server, update incrementally
  //
  update : function( m ) {
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

};







