/*

    Copyright (C) 2013 Abram Connelly

    This file is part of bleepsix v2.

    bleepsix is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    bleepsix is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with bleepsix.  If not, see <http://www.gnu.org/licenses/>.

    Parts based on bleepsix v1. BSD license
    by Rama Hoetzlein and Abram Connelly.

*/

/* Encapsulates the 'command pattern' portion of bleepsixSchBrdOp.
 */

var schBrdOpHeadless = false;
if ( typeof module !== 'undefined')
{
  schBrdOpHeadless = true;
  var bleepsixAux = require("../lib/meowaux.js");
  var guid = bleepsixAux.guid;
  var s4 = bleepsixAux.s4;
  var simplecopy = bleepsixAux.simplecopy;

}

function bleepsixSchBrdOp( schematic, board )
{
  this.schematic = schematic;
  this.board = board;

  // Global index.  Will be updated by communcation back to central DB. 
  // Initially set to -1 to indicate we don't know what the absolute index is.
  //
  this.opHistoryIndex = -1;

  // local parameters for unde/redo history.
  //
  this.opHistoryStart = 0;
  this.opHistoryEnd = -1;

  this.opHistory = [];

}

bleepsixSchBrdOp.prototype._opDebugPrint = function ( )
{
  console.log("DEBUG: g_schematic_controller.schematic.ref_lookup");
  console.log( "  opHistoryIndex: " + this.opHistoryIndex );
  console.log( "  opHistoryStart: " + this.opHistoryStart );
  console.log( "  opHistoryEnd: " + this.opHistoryEnd );
  console.log( "  opHistory.length: " + this.opHistory.length);
  console.log( this.opHistory );

}

// **************************************************************
//
//
//  Board ops
//
//
// **************************************************************


// -----------------------
//        BRD ADD
// ----------------------- 

bleepsixSchBrdOp.prototype._opBrdAddSingle = function ( type, id, data, op )
{

  var updateBBox = true;
  op = ((typeof op !== 'undefined') ? op : {} );

  if      ( type == "net" )
  {
    this.board.addNet(data.net_number, data.net_name);
    updateBBox = false;
  }

  else if ( type == "nets" )
  {
    for (var ind in data)
    {
      this.board.addNet(data[ind].net_number, data[ind].net_name);
    }
    updateBBox = false;
  }

  else if ( type == "via" )
  {
    this.board.addVia( data.x, data.y, data.width, data.layer0, data.layer1, data.net_number, id );
  }

  else if ( type == "track" )
  {
    this.board.addTrack( data.x0, data.y0, data.x1, data.y1, data.width, data.layer, data.netcode, id );
  }

  else if ( ( type == "footprintData" ) || ( type == "module" ) )
  {
   
    this.board.update_footprint_lib( data.footprintData.name, data.footprintData );
    this.board.addFootprintData( data.footprintData, data.x, data.y, id, op.idText, op.idPad  );

    var ref = this.board.refLookup( id );

    op.idText = [];
    for (var ind=0; ind<2; ind++)
    {
      op.idText.push( ref.text[ind].id );
    }

    op.idPad = [];
    for (var ind in ref.pad)
    {
      op.idPad.push( ref.pad[ind].id );
    }

  }
  else if ( type == "czone" )
  {
    this.board.addCZone( data.points, data.netcode, data.layer, data.polyscorners, id );
  }

  else if ( type == "drawsegment" )
  {
    this.board.addDrawSegment( 
        data.x0, data.y0, 
        data.x1, data.y1, 
        data.width, data.layer, id );
  }

  else if ( type == "drawarcsegment" )
  {
    this.board.addDrawArcSegment( 
        data.x, data.y, 
        data.r, 
        data.start_angle, data.end_angle,
        data.width, data.layer, id );
  }

  else
  {
    updateBBox = false;
  }

  if (updateBBox)
  {
    var ref = this.board.refLookup( id );
    if (ref)
      this.board.updateBoundingBox( ref );
    else
      console.log("bleepsixSchBrdOp._opBrdAdd: ERROR: refLookup for id " + id + 
          " failed.  Not updating bounding box");
  }

}


bleepsixSchBrdOp.prototype.opBrdAdd = function ( op, inverseFlag )
{
  inverseFlag = ( (typeof inverseFlag !== 'undefined') ? inverseFlag : false );
  var source = op.source;
  var action = op.action;
  var type = op.type;
  var data = op.data;

  if ( !( "id" in op ) )
    op.id = this.board._createId();

  if (inverseFlag)
  {

    if ( type == "net" )
    {
      this.board.removeNet( op.data.net_number );
    }
    else if (type == "nets" )
    {
      for (var ind in op.data)
      {
        this.board.removeNet( op.data[ind].net_number );
      }
    }
    else
    {
      var ref = this.board.refLookup( op.id );
      this.board.remove( { id: op.id, ref: ref } );
    }
    return;
  }

  this._opBrdAddSingle( type, op.id, data, op );

}


// ----------------------- 
//       BRD UPDATE 
// ----------------------- 

bleepsixSchBrdOp.prototype.opBrdUpdate = function ( op, inverseFlag )
{
  inverseFlag = ( (typeof inverseFlag !== 'undefined') ? inverseFlag : false );

  var source = op.source;
  var action = op.action;
  var type = op.type;
  var data = op.data;
  var id = op.id;

  if      ( type == "moveGroup" )
  {


    var id_ref_ar = [];
    for (var ind in id)
    {
      var ref = this.board.refLookup( id[ind] );
      id_ref_ar.push( { id: id[ind], ref: ref } );
    }

    var cx = op.data.cx;
    var cy = op.data.cy;
    var dx = op.data.dx;
    var dy = op.data.dy;
    var rotateCount = op.data.rotateCount;

    if (inverseFlag)
    {
      for (var ind in id_ref_ar)
      {
        this.board.relativeMoveElement( id_ref_ar[ind], -dx, -dy );
      }

      for (var i=0; (i<4) && (i<rotateCount); i++)
      {
        this.board.rotateAboutPoint90( id_ref_ar, cx, cy, true );
      }

      for (var ind in id_ref_ar)
      {
        this.board.updateBoundingBox( id_ref_ar[ind].ref );
      }

    }
    else
    {

      for (var i=0; (i<4) && (i<rotateCount); i++)
      {
        this.board.rotateAboutPoint90( id_ref_ar, cx, cy, false );
      }

      for (var ind in id_ref_ar)
      {
        this.board.relativeMoveElement( id_ref_ar[ind], dx, dy );
        this.board.updateBoundingBox( id_ref_ar[ind].ref );
      }

    }
  }
  else if (type == "rotate90")
  {

    var ccw_flag = ( inverseFlag ? (!data.ccw) : data.ccw );
    var ref = this.board.refLookup( id );

    this.board.rotate90( { id: id, ref : ref } , ccw_flag );
    this.board.updateBoundingBox( ref );
  }
  else if (type == "rotate" )
  {
    var ccw_flag = ( inverseFlag ? (!data.ccw) : data.ccw );
    var ref = this.board.refLookup( id );

    this.board.rotateAboutPoint( 
        [ { id: id, ref : ref } ] , 
        data.cx, data.cy,
        data.angle,
        ccw_flag );
    this.board.updateBoundingBox( ref );
  }

  else if (type == "flip" )
  {
    var src = data.sourceLayer;
    var dst = data.destinationLayer;

    var ref = this.board.refLookup( id );
    this.board.flip( { id: id, ref: ref } , src, dst);
  }

  else if (type == "fillczone")
  {

    if (inverseFlag)
    {

      for (var ind in id)
      {
        /*
        var ref = this.board.refLookup( id[ind] );

        // extend doesn't work the way I though it did:
        // var objA = { data: ['foo', 'bar'] };  
        // var objB = { data: [] };  
        // $.extend(true, objA, objB); 
        // console.log(objA.data); ----> ["foo", "bar"]  // Not [] !
        //
        // var objA = { data: ['foo', 'bar'] };  
        // var objB = { data: [ 'baz' ] };  
        // $.extend(true, objA, objB); 
        // console.log(objA.data); ----> ["baz", "bar"]  // Not [ "baz" ] !
        //
        ref.polyscorners = [];  

        $.extend( true, ref, data.element[ind] );
        */

        var clonedData = simplecopy( data.element[ind] );
        this.schematic.dataReplace( id[ind], clonedData );

      }

    }
    else
    {

      for (var ind in id)
      {

        var ref = this.board.refLookup( id[ind] );
        ref.polyscorners = [];
        this.board.fillCZone( ref );
      }

    }

  }

  else if (type == "mergenet")
  {

    if (!inverseFlag)
    {
      var res =
        this.board.mergeNets( data.net_number0, data.net_number1 );
      op.result = res;
    }
    else
    {
      var res = op.result;
      this.board.mergeNetsUndo( res );
    }

  }

  else if (type == "splitnet")
  {

    if (!inverseFlag)
    {
      var res =
        this.board.splitNet( data.net_number );

      op.result = res;

    } else {

      var split_res = op.result;
      if (split_res)
      {
        var orig_net_number = split_res.orig_net_number;
        var new_net = split_res.new_net;

        for (var ind in new_net)
        {
          this.board.mergeNets( orig_net_number, new_net[ind].net_number );
        }

      }

    }
  }

  else if (type == "splitnets")
  {

    if (!inverseFlag)
    {
      op.result = [];
      for (var ind in data)
      {
        var net_info = data[ind];
        var res =
          this.board.splitNet( net_info.net_number );
        op.result.push(res);
      }
    } else {

      // Reverse order
      for (var op_ind=op.result.length-1; op_ind>=0; op_ind--)
      {
        var split_res = op.result[op_ind];
        if (split_res)
        {
          var orig_net_number = split_res.orig_net_number;
          var new_net = split_res.new_net;

          for (var ind in new_net)
          {
            this.board.mergeNets( orig_net_number, new_net[ind].net_number );
          }

        }

      }

    }
  }

  else if (type == "schematicnetmap")
  {
    this.schematic.constructNet();

    var sch_pin_id_net_map = this.schematic.getPinNetMap();
    this.board.updateSchematicNetcodeMap( sch_pin_id_net_map );
    var map = this.board.kicad_brd_json.brd_to_sch_net_map;

    //HACK - DEBUG
    //this.board.updateRatsNest( undefined, undefined, map );
  }

  else if (type == "edit")
  {

    if (inverseFlag)
    {

      for (var ind=0; ind< data.oldElement.length; ind++)
      {
        var clonedData = simplecopy( data.oldElement[ind] );
        this.board.dataReplace( data.element[ind].id, clonedData );
        this.board.refUpdate( id[ind], data.oldElement[ind].id );
      }

    }
    else
    {

      // id holds array of _new_ ids.  oldElement has old id.
      // array lengths of oldelement, id and element must match.
      //
      for (var ind=0; ind<id.length; ind++)
      {

        // Update can replace a part.  This can be called from
        // a tool like toolFootprintPlace which will overwrite
        // another part that might not be cached.  Make sure
        // it's loaded into the boards local parts cache.
        //
        if (data.element[ind].type == "module")
        {
          //this.board.load_part( data.element[ind].name, data.element[ind] );
          this.board.update_footprint_lib( data.element[ind].name, data.element[ind] );
        }

        var clonedData = simplecopy( data.element[ind] );
        this.board.dataReplace( data.oldElement[ind].id, clonedData );
        this.board.refUpdate( data.oldElement[ind].id, id[ind] );

      }

    }
    
  }

}

// ----------------------- 
//       BRD DELETE
// ----------------------- 


bleepsixSchBrdOp.prototype.opBrdDelete = function ( op, inverseFlag )
{

  inverseFlag = ( (typeof inverseFlag !== 'undefined') ? inverseFlag : false );

  var source = op.source;
  var action = op.action;
  var type = op.type;
  var data = op.data;
  var id = op.id;

  if      ( type == "group" )
  {

    if (inverseFlag)
    {

      for (var ind in id )
      {
        var ref = data.element[ind];
        var _data = ref;
        if (ref.type == "module")
        {
          _data = { "footprintData" : ref, "x" : ref.x, "y" : ref.y };
        }
        else if (ref.type == "czone")
        {

          var pnts = [];
          var pc = [];
          if ( typeof ref.zcorner !== "undefined") {
            for (var ii=0; ii<ref.zcorner.length; ii++) {
               pnts.push( [ ref.zcorner[ii].x, ref.zcorner[ii].y ] );
            }
          }
          if ( typeof ref.polyscorners !== "undefined") {
            for (var ii=0; ii<ref.polyscorners.length; ii++) {
              pc.push( [ ref.polyscorners[ii].x, ref.polyscorners[ii].y ] );
            }
          }

          _data = { "points" : pnts,
                    "polyscorners" : pc,
                    netcode : ref.netcode,
                    layer : ref.layer,
                    id : ref.id  }
        }
        if ("hideFlag" in ref) { ref.hideFlag = false; }

        var type = ref.type;
        if ((type == "drawsegment") && (ref.shape == "arc"))
        {
          type = "drawarcsegment";
          _data = { "x" : ref.x, "y" : ref.y,
                    "r" : ref.r,
                    "start_angle" : ref.start_angle, "end_angle" : ref.start_angle + ref.angle,
                    "width" : ref.width, "layer" : ref.layer, "id" : id };
        }

        if ((type == "track") && (ref.shape == "through")) {

          type = "via";
          _data.x = _data.x0;
          _data.y = _data.y0;
        }

        this._opBrdAddSingle( type, ref.id, _data );
      }

    }

    else
    {

      for (var ind in id )
      {
        var ref = this.board.refLookup( id[ind] );
        this.board.remove( { id: id[ind], ref: ref } );
      }

    }

  }

}


// **************************************************************
//
//
//  Schematic ops
//
//
// **************************************************************

bleepsixSchBrdOp.prototype._undeleteComponent = function ( ref )
{
  this.schematic.addComponentData( 
      ref, 
      ref.x, ref.y, 
      ref.transform, 
      ref.id, 
      [ ref.text[0].id, ref.text[1].id ] );

  var comp = this.schematic.refLookup( ref.id );
  comp.text[0].text = ref.text[0].text;
  comp.text[0].x = ref.text[0].x;
  comp.text[0].y = ref.text[0].y;

  comp.text[1].text = ref.text[1].text;
  comp.text[1].x = ref.text[1].x;
  comp.text[1].y = ref.text[1].y;
}


bleepsixSchBrdOp.prototype._opSchAddSingle = function ( type, id, data, op )
{
  var updateBBox = true;
  op = ((typeof op !== 'undefined') ? op : {} );

  if      ( type == "connection" )
  {
    this.schematic.addConnection( data.x, data.y, id ); 
  }

  else if ( type == "noconn" )
  {
    this.schematic.addNoconn( data.x, data.y, id ); 
  }

  else if ( type == "componentData" )
  {
    //EXPERIMENTAL
    this.schematic.load_part( data.componentData.name, data.componentData );

    this.schematic.addComponentData( data.componentData, data.x, data.y, data.transform, id, op.idText  );
  }

  else if ( type == "component" )
  {
    this.schematic.addComponent( data.name, data.x, data.y, data.transform, id, op.idText );
  }

  else if ( type == "wireline" )
  {
    this.schematic.addWire( data.startx, data.starty, data.endx, data.endy, id );
  }

  else if ( type == "busline" )
  {
    console.log("bleepsixSchBrdOp.opSchAdd busline not implemented\n");
    updateBBox = false;
  }
  else if ( type == "entrybusbus" )
  {
    console.log("bleepsixSchBrdOp.opSchAdd entrybusbus not implemented\n");
    updateBBox = false;
  }
  else if ( type == "textnote" )
  {
    console.log("bleepsixSchBrdOp.opSchAdd textnote not implemented\n");
    updateBBox = false;
  }
  else if ( type == "label" )
  {
    this.schematic.addLabel( data.text, data.x, data.y, data.orientation, data.dimension, id);
  }
  else if ( type == "labelglobal" )
  {
    console.log("bleepsixSchBrdOp.opSchAdd labelglobal not implemented\n");
    updateBBox = false;
  }
  else if ( type == "labelheirarchical" )
  {
    console.log("bleepsixSchBrdOp.opSchAdd labelheirarchical not implemented\n");
    updateBBox = false;
  }
  else
  {
    updateBBox = false;
  }

  if (updateBBox)
  {
    var ref = this.schematic.refLookup( id );
    if (ref)
    {
      if ("boundingd_box" in ref)
        this.schematic.updateBoundingBox( ref );
    }
    else
      console.log("bleepsixSchBrdOp._opSchAdd: ERROR: refLookup for id " + id + " failed.  Not updating bounding box");
  }

}

//

//-- ADD

bleepsixSchBrdOp.prototype.opSchAdd = function ( op, inverseFlag )
{
  inverseFlag = ( (typeof inverseFlag !== 'undefined') ? inverseFlag : false );
  var source = op.source;
  var action = op.action;
  var type = op.type;
  var data = op.data;

  if ( !( "id" in op ) )
    op.id = this.schematic._createId();

  if (inverseFlag)
  {
    var ref = this.schematic.refLookup( op.id );
    this.schematic.remove( { id: op.id, ref: ref } );
    return;
  }

  this._opSchAddSingle( type, op.id, data, op );

}
//-- UPDATE 

bleepsixSchBrdOp.prototype.opSchUpdate = function ( op, inverseFlag )
{
  inverseFlag = ( (typeof inverseFlag !== 'undefined') ? inverseFlag : false );

  var source = op.source;
  var action = op.action;
  var type = op.type;
  var data = op.data;
  var id = op.id;

  if      ( type == "componentRotate90" )
  {
    var ccw_flag = ( inverseFlag ? (!data.ccw) : data.ccw );
    var ref = this.schematic.refLookup( id );

    //this.schematic.rotate90( { id: id, ref : ref } , op.ccw );
    this.schematic.rotate90( { id: id, ref : ref } , ccw_flag );

    this.schematic.updateBoundingBox( ref );
  }

  else if ( type == "componentRotate180" )
  {
    var ccw_flag = ( inverseFlag ? (!data.ccw) : data.ccw );

    var ref = this.schematic.refLookup( id );

    //this.schematic.rotate90( { id: id, ref : ref } , op.ccw );
    //this.schematic.rotate90( { id: id, ref : ref } , op.ccw );
    this.schematic.rotate90( { id: id, ref : ref } , ccw_flag );
    this.schematic.rotate90( { id: id, ref : ref } , ccw_flag );

    this.schematic.updateBoundingBox( ref );
  }

  else if ( type == "componentFlip" )
  {
    var ref = this.schematic.refLookup( id );
    this.schematic.flip( { id: id, ref: ref } );
    this.schematic.updateBoundingBox( ref );
  }

  else if ( type == "edit" )
  {

    if (inverseFlag)
    {

      //console.log("opSchUpdate edit inverse: length: " + data.oldElement.length);
      //console.log( data.oldElement );

      for (var ind=0; ind< data.oldElement.length; ind++)
      {
        //var ref = this.schematic.refLookup( data.element[ind].id );
        ////$.extend( true, ref, data.oldElement[ind].ref );
        //$.extend( true, ref, data.oldElement[ind] );

        /*
        var clonedData = simplecopy( data.oldEelement[ind].ref );
        this.schematic.dataReplace( data.oldElement[ind].id, clonedData );
        this.schematic.refUpdate( id[ind], data.oldElement[ind].id );
        */
        var clonedData = simplecopy( data.oldElement[ind].ref );
        this.schematic.dataReplace( data.oldElement[ind].id, clonedData );
        this.schematic.refUpdate( id[ind], data.oldElement[ind].id );
      }

    }
    else
    {

      // id holds array of _new_ ids.  oldElement has old id.
      // array lengths of oldelement, id and element must match.
      //
      for (var ind=0; ind<id.length; ind++)
      {
        //var ref = this.schematic.refLookup( data.oldElement[ind].id );
        //$.extend( true, ref, data.element[ind] );
        //this.schematic.refUpdate( data.oldElement[ind].id, id[ind] );

        var clonedData = simplecopy( data.element[ind].ref );
        this.schematic.dataReplace( data.oldElement[ind].id, clonedData );
        this.schematic.refUpdate( data.oldElement[ind].id, id[ind] );

      }

    }

  }
  else if ( type == "moveGroup" )
  {

    var id_ref_ar = [];
    for (var ind in id)
    {
      var ref = this.schematic.refLookup( id[ind] );
      id_ref_ar.push( { id: id[ind], ref: ref } );
    }

    var cx = op.data.cx;
    var cy = op.data.cy;
    var dx = op.data.dx;
    var dy = op.data.dy;
    var rotateCount = op.data.rotateCount;

    if (inverseFlag)
    {
      for (var ind in id_ref_ar)
      {
        this.schematic.relativeMoveElement( id_ref_ar[ind], -dx, -dy );
      }

      for (var i=0; (i<4) && (i<rotateCount); i++)
      {
        this.schematic.rotateAboutPoint90( id_ref_ar, cx, cy, true );
      }

      for (var ind in id_ref_ar)
      {
        this.schematic.updateBoundingBox( id_ref_ar[ind].ref );
      }

    }
    else
    {

      for (var i=0; (i<4) && (i<rotateCount); i++)
      {
        this.schematic.rotateAboutPoint90( id_ref_ar, cx, cy, false );
      }

      for (var ind in id_ref_ar)
      {
        this.schematic.relativeMoveElement( id_ref_ar[ind], dx, dy );
        this.schematic.updateBoundingBox( id_ref_ar[ind].ref );
      }

    }

  }

  else if ( type == "updateComponent")
  {

    if (inverseFlag)
    {

      for (var ind=0; ind< data.oldElement.length; ind++)
      {
        var clonedData = simplecopy( data.oldElement[ind].ref );
        this.schematic.dataReplace( clonedData, id[ind] );
      }

    }
    else
    {

      // id holds array of _new_ ids.  oldElement has old id.
      // array lengths of oldelement, id and element must match.
      //
      for (var ind=0; ind<id.length; ind++)
      {

        //EXPERIMENTAL
        this.schematic.load_part( data.element[ind].ref.name, data.element[ind].ref );

        var clonedData = simplecopy( data.element[ind].ref );
        this.schematic.updateComponentData( clonedData, id[ind] );
      }

    }


  }

  else if ( type == "net" )
  {

    // EXPERIMENTAL
    this.schematic.constructNet();
    var x = this.schematic.getPinNetMap();
    this.schematic.updateNets( x );
    // EXPERIMENTAL

    //this.schematic.updateNets( data );
  }

  else if (type == "boardnetmap")
  {

    console.log("WARNING: opSchUpdate boardnetmap not implemented");

    //this.schematic.getPinNetMap();
    //this.board.updateSchematicNetcodeMap( sch_pin_id_net_map );
  }

  else if (type == "schematicnetmap")
  {
    this.schematic.constructNet();
    var sch_pin_id_net_map = this.schematic.getPinNetMap();

    this.board.updateSchematicNetcodeMap( sch_pin_id_net_map );
    var map = this.board.kicad_brd_json.brd_to_sch_net_map;

    //HACK - DEBUG
    //this.board.updateRatsNest( undefined, undefined, map );
  }


}


//-- DELETE

bleepsixSchBrdOp.prototype.opSchDelete = function ( op, inverseFlag )
{
  inverseFlag = ( (typeof inverseFlag !== 'undefined') ? inverseFlag : false );

  var source = op.source;
  var action = op.action;
  var type = op.type;
  var data = op.data;
  var id = op.id;

  if      ( type == "group" )
  {

    if (inverseFlag)
    {

      for (var ind in id )
      {
        var ref = data.element[ind];

        if ( ref.type == "component" )
        {
          this._undeleteComponent( ref );
        }
        else
        {
          this._opSchAddSingle( ref.type, ref.id, ref );
        }
      }

    }

    else
    {

      for (var ind in id )
      {
        var ref = this.schematic.refLookup( id[ind] );
        this.schematic.remove( { id: id[ind], ref: ref } );
      }

    }

  }

}



//bleepsixSchBrdOp.prototype.opCommand = function ( op, inverseFlag, replayFlag )
bleepsixSchBrdOp.prototype.opCommand = function ( op )
{
  inverseFlag = ( (typeof op.inverseFlag !== 'undefined') ? op.inverseFlag : false );
  replayFlag = ( (typeof op.replayFlag !== 'undefined') ? op.replayFlag : false );

  var source = op.source;
  var dest = op.destination;
  var action = op.action;
  var type = op.type;
  var data = op.data;

  // Save result if we're undoing
  //
  if (!inverseFlag) { op.result = {}; }

  // So we don't add the undo/redo onto our history stack while
  // we're undoing.
  //
  if (!replayFlag)
  {
    this.opHistoryEnd++;
    var end = this.opHistoryEnd;
    var hist = this.opHistory;

    if ( end < hist.length ) { hist[ end ] = op; }
    else                     { hist.push( op ); }

    this.opHistory = hist.slice(0, end+1);

  }

  if (this.opHistoryIndex >= 0)
    this.opHistoryIndex++;

  if ( dest == "sch" )

  {
    if      ( action == "add" )    { this.opSchAdd( op, inverseFlag ); }
    else if ( action == "update" ) { this.opSchUpdate( op, inverseFlag ); }
    else if ( action == "delete" ) { this.opSchDelete( op, inverseFlag ); }
  }

  else if ( dest == "brd" )
  {
    if      ( action == "add" )    { this.opBrdAdd( op, inverseFlag ); }
    else if ( action == "update" ) { this.opBrdUpdate( op, inverseFlag ); }
    else if ( action == "delete" ) { this.opBrdDelete( op, inverseFlag ); }
  }

}


bleepsixSchBrdOp.prototype.opUndo = function( src )
{
  console.log("opUndo");

  if ( this.opHistoryEnd >= 0 )
  {

    var start_group_id = this.opHistory[ this.opHistoryEnd ].groupId ;
    while ( ( this.opHistoryEnd >= 0 ) &&
            ( this.opHistory[ this.opHistoryEnd ].groupId == start_group_id ) )
    {
      this.opCommand( this.opHistory[ this.opHistoryEnd ] );
      this.opHistoryEnd--;
    }

  }
  else
  {
    console.log("bleepsixSchBrdOp.opUndo: already at first element, can't undo any further");
  }

}

bleepsixSchBrdOp.prototype.opRedo = function( src )
{
  console.log("opRedo");

  if ( this.opHistoryEnd < (this.opHistory.length-1) )
  {

    var start_group_id = this.opHistory[ this.opHistoryEnd+1 ].groupId;
    while ( (this.opHistoryEnd < (this.opHistory.length-1) ) &&
            (this.opHistory[ this.opHistoryEnd+1 ].groupId == start_group_id) )
    {
      this.opHistoryEnd++;
      this.opCommand( this.opHistory[ this.opHistoryEnd ] )
    }
  }
  else
  {
    console.log("bleepsixSchBrdOp.opRedo: already at last element, can't redo any further");
  }

}

if ( typeof module !== 'undefined')
{
  module.exports = bleepsixSchBrdOp ;
}


