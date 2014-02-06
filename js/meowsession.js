var bleepsixSchematicController = require("../../bleepsix/js/sch/bleepsixSchematicController.js");
var redis = require('redis'),
    db = redis.createClient();


var activeSession = {};
var projectListener = {};
var projectListenerCount = {};
var projectListenerController = {};

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
  }catch (e)
  {
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
  dispatch_op : dispatch_op,
  load_snapshot : load_snapshot,
  registerSession : registerSession,
  registerProject : registerProject,
  remove : remove,
  debug_print : debug_print
};

