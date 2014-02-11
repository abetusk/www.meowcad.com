var bleepsixSchematicController = require("../../bleepsix/js/sch/bleepsixSchematicController.js");
var redis = require('redis'),
    db = redis.createClient();


var activeSession = {};
var projectListener = {};
var projectListenerCount = {};
var projectListenerController = {};

var g_auth = null;
var g_proj = null;
var g_aux = null;

function init( auth, aux, proj )
{
  g_auth = auth;
  g_aux = aux;
  g_proj = proj;
}

function save_snapshot(err, data, projectId)
{

}

function load_snapshot(err, data, projectId)
{
  if (err)
  {
    console.log("ERROR: ("+ projectId + ") " + err);
    return;
  }

  var json_sch = {};
  var json_brd = {};
  try {
    json_sch = JSON.parse( data.json_sch );
    json_brd = JSON.parse( data.json_brd );
  } 
  catch (e)
  {
    console.log("ERROR: meowsession.load_snapshot could not parse json_sch or json_brd:");
    console.log(e);
    return;
  }

  console.log("loading snapshot for " + projectId + ":" );
  console.log(json_sch);
  console.log(json_brd);

  var c = projectListenerController[projectId];
  c.schematic.load_schematic( json_sch );
  c.board.load_board( json_brd );

  console.log("loaded snapshot for " + projectId + ":" );
  console.log(c.schematic.kicad_sch_json);
  console.log(c.board.kicad_brd_json);

}

function remove( transactionId )
{
  if ("projectId" in activeSession[transactionId])
  {
    var projId = activeSession[transactionId].projectId;

    console.log("  found projectId, " + projId + ", deleting from projectListener");

    delete projectListener[ projId ][transactionId];

    projectListenerCount[projId]--;
    if (projectListenerCount[projId] == 0)
    {
      delete projectListenerCount[projId];
      delete projectListener[projId];
    }

  }

  delete activeSession[transactionId];

}

function registerSession( transactionId, socket, db  )
{
  activeSession[transactionId] = { authenticated : false, socket : socket, db : db,  };
}


function registerProject( transactionId, projectId, socket )
{
  activeSession[transactionId].projectId = projectId;

  if (!(projectId in projectListener))
  {
    projectListener[projectId] = {};
    projectListenerCount[projectId] = 0;
    projectListenerController[projectId]  = new bleepsixSchematicController();

    db.hgetall( "projectsnapshot:" + projectId, function(err, data) { load_snapshot( err, data, projectId); } );

  }
  projectListener[projectId][transactionId] = socket;
  projectListenerCount[projectId]++;

}

function debug_print()
{
  console.log("projectListenerPrint:");
  for (var proj in projectListener)
  {
    console.log("  (projectId) " + proj + " [count: " + projectListenerCount[proj] + "] " );
    for (var tid in projectListener[proj])
    {
      console.log("    (transactionId) " + tid);
    }
  }
  console.log("\n\n");
}




function dispatch_op( transactionId, socket, db, data )
{

  console.log("dispatch_op: " + transactionId);

  if ( "projectId" in data )
  {
    var projectId = data.projectId;

    console.log("displatch_op projectId: " + data.projectId);
    if ( projectId in projectListener )
    {

      //update local copy
      if (projectId in projectListenerController)
      {

        console.log("info: updating projectId " + projectId + " from projectListenerController");
        console.log("info: op: (" + (typeof data.op) + ")"  );
        console.log(data.op);

        var c = projectListenerController[projectId];

        /*
        console.log("\n\n\n------------------------------------------------------\n");
        console.log("BEFORE c.board.kicad_brd_json:\n");
        console.log( JSON.stringify(c.board.kicad_brd_json, undefined, 2 ) );
        console.log("\n------------------------------------------------------\n\n\n\n");
        */

        c.op.opCommand( data.op );

        console.log("info: saving snapshot");
        db.hmset( "projectsnapshot:" + projectId, 
            {
              json_sch : JSON.stringify( c.schematic.kicad_sch_json ),
              json_brd : JSON.stringify( c.board.kicad_brd_json )
            });

        /*
        console.log("\n\n\n------------------------------------------------------\n");
        console.log("AFTER c.board.kicad_brd_json:\n");
        console.log( JSON.stringify(c.board.kicad_brd_json, undefined, 2 ) );
        console.log("\n------------------------------------------------------\n\n\n\n");
        */

      }
      else
      {
        console.log("ERROR: could not find projectId " + projectId + " in projectListenerController!");
      }

      for (var tid in projectListener[projectId])
      {
        if (tid == transactionId)
        {
          console.log("  skipping " + tid);
        }
        else
        {
          var s = projectListener[projectId][tid];
          console.log("  SENDING data to " + tid);

          data.op.scope = "local";

          s.emit("projectop", { type: "op", message:"push from server", op: data.op } );
          console.log("\n\n\n\n\n");
        }
      }
    }
  }

}


setInterval( debug_print, 5000 );

module.exports = {
  init : init,
  dispatch_op : dispatch_op,
  load_snapshot : load_snapshot,
  registerSession : registerSession,
  registerProject : registerProject,
  remove : remove,
  debug_print : debug_print
};

