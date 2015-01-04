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

  console.log("session id:");
  console.log( sessHash );

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
      socket.emit( msgParent, { type:"response", status: "error", message: "authentication failure (1)" } );
      return;
    }

    dbUserId = d.userId;
    if (dbUserId != userId )
    {
      socket.emit( msgParent, { type:"response", status: "error", message: "authentication failure (2)" } );
      return;
    }

    if (d.active != 1)
    {
      socket.emit( msgParent, { type:"response", status: "error", message: "authentication failure (3)" } );
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
      socket.emit( msgParent, { type:"response", status: "error", message: "invalid project (1)" } );
      return;
    }

    //console.log(d);
    console.log("userId: " + userId + " dbUserId: " + d.userId );

    if (d.userId != userId)
    {
      socket.emit( msgParent, { type:"response", status: "error", message: "invalid project (2)" } );
      return;
    }

    //console.log("active? " + d.active);

    if (d.active != 1)
    {
      socket.emit( msgParent, { type:"response", status: "error", message: "invalid project (3)" } );
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

function inputProjectCheck( m )
{
  var userId = m.data.userId;
  var sessionId = m.data.sessionId;
  var projectId = m.data.projectId;
  var msgParent = m.messageParent;

  if ( (typeof userId === 'undefined') ||
       (typeof sessionId === 'undefined') ||
       (typeof projectId === 'undefined')  )
  {
    m.socket.emit(msgParent,  { 
      type: "response", 
      status: "error", 
      message : "userId, sessionId or projectId undefined" });
    return 0;
  }
  return 1;
}

/*
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
*/

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

  projectAuth: function( m ) {
    console.log("meowproject projectauth");

    m.messageParent = "projectauth";

    if (!inputProjectCheck( m ))
      return;

    async.waterfall([
      fSessionGet( m ),
      fValidateSession( m ),
      function(d, callback) {

        console.log("trying to fetch project: " + m.data.projectId );

        m.db.hgetall( "project:" + m.data.projectId, callback );
      },
      fValidateItem( m ),
      function( d, callback )
      {
        console.log("fetching project snapshot");

        m.transportData = { projectData : d } ;

        m.db.hgetall( "projectsnapshot:" + m.data.projectId, callback);
      },
      function(d, callback)
      {
        console.log("ok!");
        //console.log(d);

        m.socket.emit("projectauth", 
          { type:"response", 
            status:"success", 
            message:"ok!", 
            json_sch : d.json_sch, 
            json_brd : d.json_brd,
            projectName : m.transportData.projectData.name,
            projectId : m.data.projectId
          });

        m.callback( m.transactionId, m.data.projectId, m.socket );
      }
      ],
      function( err, result) {
        console.log("schauth error");
        console.log(err);
        console.log(result);
      });
  },

  projectFlush: function( m ) {
    console.log("project flush");
    m.messageParent = "projectflush";

    async.waterfall([
      fSessionGet( m ),
      fValidateSession( m ),
      function(d, callback) {
        m.db.hgetall( "project:" + m.data.projectId, callback );
      },
      fValidateItem( m ),
      function( d, callback )
      {
        m.db.hmset( "projectsnapshot:" + m.data.projectId,
          {
            json_sch : m.data.json_sch,
            json_brd : m.data.json_brd
          });
        m.socket.emit("projectflush", { type:"response", status:"success", message:"ok!" });
      }
      ],
      function( err, result) {
        console.log("projectflush error");
        console.log(err);
        console.log(result);
      });
  },

  projectSnapshot: function( m ) {
    console.log("project snapshot");
    m.messageParent = "projectsnapshot";

    async.waterfall([
      fSessionGet( m ),
      fValidateSession( m ),

      function(d, callback) {
        m.db.hgetall( "project:" + m.data.projectId, callback );
      },

      fValidateItem( m ),

      function( d, callback )
      {
        m.db.hgetall( "projectsnapshot:" + m.data.projectId, callback )
      },

      function( d, callback )
      {
        if (!d)
        {
          console.log("error occured while fetching snapshot");
          m.socket.emit("projectsnapshot", { type:"response", status:"failure", message:"no snapshot data" });
          return;
        }

        var msg = 
          {
            json_sch : d.json_sch,
            json_brd : d.json_brd
          };
        m.socket.emit("projectsnapshot", { type:"response", status:"success", message:"ok!", data : msg });
      }
      ],

      function( err, result) {
        console.log("projectsnapshot error");
        console.log(err);
        console.log(result);
      });
  },

  projectOp: function( m ) {
    console.log("project op");
    m.messageParent = "projectop";

    async.waterfall([
      fSessionGet( m ),
      fValidateSession( m ),
      function(d, callback) {
        m.db.hgetall( "project:" + m.data.projectId, callback)
      },
      fValidateItem(m),
      function(d, callback) {
        m.data.eventId = guid();
        m.db.rpush( "projectevent:" + m.data.projectId, m.data.eventId );
        m.db.hmset( "projectop:" + m.data.projectId + ":" + m.data.eventId,
          { data: JSON.stringify(m.data.op) });

        //console.log("pushing m.data.op:");
        //console.log( JSON.stringify(m.data.op) );

        m.socket.emit( "projectop", { type:"response", status:"success", message:"ok!", eventId: m.data.eventId });
      }
      ],
      function( err, result) {
        console.log("projectop error");
        console.log(err);
        console.log(result);
      });
  },

  newProject : function( m ) {
    console.log("meowproject newproject");
    m.messageParent = "newproject";

    var projName = 
      ( (typeof m.data.projectName === 'undefined') ? randomName(json_words.word, 3) : m.data.projectName );

    /*
    var schName =
      ( (typeof m.data.schematicName === 'undefined') ? randomName(json_words.word, 3) : m.data.schematicName );
    var brdName =
      ( (typeof m.data.boardName === 'undefined') ? randomName(json_words.word, 3) : m.data.boardName );
      */

    if (!inputCheck( m )) 
      return;

    async.waterfall([
      fSessionGet( m ),
      fValidateSession( m ),
      function(d, callback) {
        var userId = m.data.userId;
        m.db.hgetall( "user:" + String(userId), callback );
      },
      function(d, callback) {
        if (!d)
        {
          m.socket.emit("newproject", 
            { type:"response",
              status:"error",
              message:"no data on user"
            });
          return;
        }

        if (d.type == "anonymous")
        {
          m.socket.emit("newproject", 
            { type:"response",
              status:"error",
              message:"anonymous users cannot create new projects"
            });
          return;
        }

        callback(null, d);
      },
      function(d, callback) {

        var userId = m.data.userId;

        var projId = guid();

        console.log( "userId: " + String(userId) + ", projId: " + projId);

        m.db.rpush( "olio:" + String(userId), projId );
        m.db.hmset( "project:" + projId, 
          { id: projId, 
            userId : userId, 
            name: projName,
            //schematicName: schName,
            //boardName: brdName,
            permission:"user", 
            active : "1"
          });

        m.db.rpush( "projectevent:" + projId, "0" );

        var default_net_parameter = 
        {
         "Default" : {
           "name" : "Default",
           "description" : "This is the default net class.",
           "unit" : "deci-thou",
           "track_width" : 100,
           "clearance" : 100,
           "via_diameter" : 472,
           "via_drill_diameter" : 250,
           "uvia_diameter" : 200,
           "uvia_drill_diameter" : 50,
           "net" : [ ]
           }
        };


        var schematic_data = {
          element: [],
          component_lib : {},
          net_pin_id_map : {}
        };

        var board_data = { 
          element: [], 
          equipot: [ { net_name : "", net_number : 0 }],  
          units: "deci-mils", 
          net_class: default_net_parameter
        };


        m.db.hmset( "projectop:" + projId  + ":0",
            { id: projId,
              type : "snapshot",
              schematicData : JSON.stringify( schematic_data ),
              boardData : JSON.stringify( board_data ),

              /*
              schematicData : "{ \"element\" : [] }",
              boardData : "{ \"element\" : [], \"equipot\" : [], " + 
                    " \"equipot\" : [ { \"net_name\" : \"\", \"net_number\" : 0 }], " + 
                    " \"units\" : \"deci-mils\" " +
                    default_net_parameter + 
              " }",
              */

              ind : 0
            });

        m.db.hmset( "projectsnapshot:" + projId  ,
            { id: projId,
              schematicData : JSON.stringify( schematic_data ),
              boardData : JSON.stringify( board_data ),

              /*
              schematicData : "{ \"element\" : [] }",
              boardData : "{ \"element\" : [], " + 
                    " \"equipot\" : [ { \"net_name\" : \"\", \"net_number\" : 0 }], " + 
                    " \"units\" : \"deci-mils\" "
                    default_net_parameter + 
                    "}",
                    */
              ind : 0
            });

        console.log("newproject created");

        m.db.sadd( "projectpool", projId );


        m.socket.emit("newproject", {
                type:"response",
                status:"success",
                message:"new project created",
                projectId: projId
        });

        m.callback( m.transactionId, projId, m.socket );
        console.log("finishing");
      }
      ],
      function( err, result) {
        console.log("newproject error");
        console.log(err);
        console.log(result);
      });
  }

};







