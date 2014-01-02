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


module.exports = {

  s4 : s4,
  guid : guid,

  picReady : function( m ) {
    var userId = m.data.userId;
    var sessionId = m.data.sessionId;
    var clientToken = m.data.clientToken;
    var socket = m.socket;
    var db = m.db;

    if ( ( typeof userId !== 'undefined') &&
         ( typeof sessionId !== 'undefined') )
    {
      socket.emit("picready", { type : "response", status : "error", message: "authorization failure" });
    }

    console.log("picReady starting, userid: " + userId + ", sessionId: " + sessionId);
    async.waterfall([

      function(callback)
      {
        var sha512 = crypto.createHash('sha512');
        var sessHash = sha512.update( userId + sessionId ).digest('hex');
        db.hgetall( "session:" + sessHash, callback);
      },

      function ( d, callback )
      {

        if ( (!d) || (d.active != "1") )
        {
          socket.emit("picready", { type:"response", status:"error", message:"access denied" });
          return;
        }


        console.log("calling redis hgetall on pic:" + picId);

        db.hgetall( "message:" + clientToken, callback );
      },

      function( d, callback )
      {

        // message lookup failed
        //
        if (!d)
        {
          socket.emit("picready", { type : "response", status : "error", message: "nonexistent or unauthorized" });
          return;
        }

        var picId = d.picId;

        db.hgetall( "pic:" + picId, callback );
      },

      function( d, callback ) 
      {
        if (!d)
        {
          socket.emit("picready", { type : "response", status : "error", message: "nonexistent or unauthorized" });
          return;
        }

        // Pic found, see if it's owned by the user
        //
        if ( d.userId != userId )
        {
          socket.emit("picready", { type : "response", status : "error", message: "nonexistent or unauthorized" });
          return;
        }

        // If it's world readable, send back a message, filling the editPermission appropriately
        //
        socket.emit("picready", { 
          type : "response", 
          status : "success", 
          message: "ready", 
          picId : d.picId
        });
        return;

      }

    ],
    function (err,result) {
      console.log("picPermission error:");
      console.log(err);
      console.log(result);
    });

  },
  
  picPermission : function( m ) {
    var userId = m.data.userId;
    var sessionId = m.data.sessionId;
    var picId = m.data.picId;
    var socket = m.socket;
    var db = m.db;

    var anonymousRequest = true;
    if ( ( typeof userId !== 'undefined') &&
         ( typeof sessionId !== 'undefined') )
      anonymousRequest = false;

    console.log("picPermission starting, userid: " + userId + ", sessionId: " + sessionId);

    /*
    var userRequest = false;
    if ( (typeof userId !== 'undefined') &&
         (typeof sessionId !== 'undefined') )
    {
      userRequest = true;
    }
    */

    if (anonymousRequest)
    {
      async.waterfall([
        function(callback)
        {
          db.hgetall( "pic:" + picId, callback );
        },
        function( d, callback )
        {

          if (!d)
          {
            socket.emit("picpermission", { type : "response", status : "error", message: "nonexistent or unauthorized" });
            return;
          }

          var picUserId = d.userId;
          var picPermission = d.permission;

          if ( picPermission == "world-read") 
          {
            socket.emit("picpermission", { 
              type : "response", 
              status : "success", 
              message: "ready", 
              editPermission: "denied" 
            });
            return;
          }

          socket.emit("picpermission", { type : "response", status : "error", message: "nonexistent or unauthorized" });

        }

      ],
      function (err,result) {
        console.log("picPermission error:");
        console.log(err);
        console.log(result);
      } );

      return;
    }

    // We have a sessionid, so we need to authenticate the request
    //
    async.waterfall([
      function(callback)
      {

        var sha512 = crypto.createHash('sha512');
        var sessHash = sha512.update( userId + sessionId ).digest('hex');
        db.hgetall( "session:" + sessHash, callback);

      },
      function ( d, callback )
      {

        if ( (!d) || (d.active != "1") )
        {
          socket.emit("picpermission", { type:"response", status:"error", message:"access denied" });
          return;
        }


        console.log("calling redis hgetall on pic:" + picId);

        db.hgetall( "pic:" + picId, callback );
      },
      function( d, callback )
      {

        // Pic lookup failed
        //
        if (!d)
        {
          socket.emit("picpermission", { type : "response", status : "error", message: "nonexistent or unauthorized" });
          return;
        }

        var picUserId = d.userId;
        var picPermission = d.permission;

        // Pic found, see if it's owned by the user
        //
        perm = "denied";
        if ( picUserId == userId )
        {
          perm = "allowed";
        }

        // If it's world readable, send back a message, filling the editPermission appropriately
        //
        if ( picPermission == "world-read" )
        {
          socket.emit("picpermission", { 
            type : "response", 
            status : "success", 
            message: "ready", 
            permission: picPermission,
            editPermission: perm
          });
          return;
        }

        // Not owned by user, give back an error message
        //
        if (picUserId != d.userId) 
        {
          socket.emit("picpermission", { type : "response", status : "error", message: "nonexistent or unauthorized" });
          return;
        }

        socket.emit("picpermission", { 
          type : "response", 
          status : "success", 
          message: "ready", 
          permission: picPermission,
          editPermission: perm
        });
        return;

      }

    ],
    function (err,result) {
      console.log("picPermission error:");
      console.log(err);
      console.log(result);
    });

  },

  picAccess : function( m )
  {
    var db          = m.db;
    var socket      = m.socket;

    var picId       = m.data.picId;
    var userId      = m.data.userId;
    var sessionId   = m.data.sessionId;
    var picPermission = m.data.permission;

    console.log(m.data);

    if ( ( typeof picPermission === 'undefined' ) ||
         ( typeof picId === 'undefined' ) ||
         ( typeof userId === 'undefined' ) ||
         ( typeof sessionId === 'undefined' ) )
    {
      socket.emit("picaccess", { type:"response", status: "error", message: "access denied (0)" });
      return;
    }

    async.waterfall([
      function(callback) {

        var sha512 = crypto.createHash('sha512');
        var sessHash = sha512.update( userId + sessionId ).digest('hex');

        db.hgetall( "session:" + sessHash , callback );
      },
      function(d, callback) {

        if ( (!d) || (d.active != "1") )
        {
          socket.emit("picaccess", { type:"response", status: "error", message: "access denied (1)" });
          return;
        }

        db.hgetall( "pic:" + picId, callback );
      },
      function(d, callback)
      {
        if (!d)
        {
          socket.emit("picaccess", { type:"response", status: "error", message: "access denied (2)" });
          return;
        }

        var picUserId = d.userId;

        if ( picUserId != userId )
        {
          socket.emit("picaccess", { type:"response", status: "error", message: "access denied (3)" });
          return;
        }

        if (picPermission == "world-read")
        {
          db.hmset( "pic:" + picId, { permission: "world-read" });
        }
        else if (picPermission == "user")
        {
          db.hmset( "pic:" + picId, { permission: "user" });
        }
        else
        {
          // user is authenticaed, so giving a useful error message doesn't leak 
          // unauthorized information.
          //
          socket.emit("picaccess", { type:"response", status: "error", message: "invalid permission" });
          return;
        }

        socket.emit("picaccess", { type:"response", status:"success", message: "permission changed" });

      }
    ],
    function(err, result) {
    });
  }

};







