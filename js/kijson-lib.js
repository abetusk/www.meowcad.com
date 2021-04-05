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


function s4() {
  return Math.floor((1 + Math.random()) * 0x10000)
             .toString(16)
             .substring(1);
};

function guid() {
  return s4() + s4() + '-' +
         s4() + '-' +
         s4() + '-' +
         s4() + '-' + s4() + s4() + s4();
}

function pretty_netname(nc) {
  var s_nc = nc.toString();
  return "N-0" + s_nc;
}

function _join_sch_brd(sch, brd, _id) {
  _id = ((typeof _id === "undefined") ? guid() : _id);
  return { "id" : _id, "json_sch" : sch, "json_brd" : brd };
}

function _merge_project(_proja, _projb) {

  var proja = Object.assign({}, _proja);
  var projb = Object.assign({}, _projb);

  var proj = [ proja, projb ];
  var bbox_sch = [ [ [0,0],[0,0] ],
                   [ [0,0],[0,0] ] ];
  var bbox_brd = [ [ [0,0],[0,0] ],
                   [ [0,0],[0,0] ] ];
  var _init_sch = [ false, false ];
  var _init_brd = [ false, false ];

  // find bounding boxes for schematic and boards
  //
  for (var proj_idx=0; proj_idx<proj.length; proj_idx++) {

    var _p = proj[proj_idx];
    var _sch = _p.json_sch;
    var _brd = _p.json_brd;

    for (var ele_idx=0; ele_idx < _sch.element.length; ele_idx++) {
      var ele = _sch.element[ele_idx];
      if (!("bounding_box" in ele)) { continue; }

      if (!_init_sch[proj_idx]) {
        bbox_sch[proj_idx][0][0] = ele.bounding_box[0][0];
        bbox_sch[proj_idx][0][1] = ele.bounding_box[0][1];
        bbox_sch[proj_idx][1][0] = ele.bounding_box[1][0];
        bbox_sch[proj_idx][1][1] = ele.bounding_box[1][1];
      }
      _init_sch[proj_idx] = true;

      if (bbox_sch[proj_idx][0][0] > ele.bounding_box[0][0]) { bbox_sch[proj_idx][0][0] = ele.bounding_box[0][0]; }
      if (bbox_sch[proj_idx][0][1] > ele.bounding_box[0][1]) { bbox_sch[proj_idx][0][1] = ele.bounding_box[0][1]; }
      if (bbox_sch[proj_idx][1][0] < ele.bounding_box[1][0]) { bbox_sch[proj_idx][1][0] = ele.bounding_box[1][0]; }
      if (bbox_sch[proj_idx][1][1] < ele.bounding_box[1][1]) { bbox_sch[proj_idx][1][1] = ele.bounding_box[1][1]; }

    }

    for (var ele_idx=0; ele_idx < _brd.element.length; ele_idx++) {
      var ele = _brd.element[ele_idx];
      if (!("bounding_box" in ele)) { continue; }

      if (!_init_brd[proj_idx]) {
        bbox_brd[proj_idx][0][0] = ele.bounding_box[0][0];
        bbox_brd[proj_idx][0][1] = ele.bounding_box[0][1];
        bbox_brd[proj_idx][1][0] = ele.bounding_box[1][0];
        bbox_brd[proj_idx][1][1] = ele.bounding_box[1][1];
      }
      _init_brd[proj_idx] = true;

      if (bbox_brd[proj_idx][0][0] > ele.bounding_box[0][0]) { bbox_brd[proj_idx][0][0] = ele.bounding_box[0][0]; }
      if (bbox_brd[proj_idx][0][1] > ele.bounding_box[0][1]) { bbox_brd[proj_idx][0][1] = ele.bounding_box[0][1]; }
      if (bbox_brd[proj_idx][1][0] < ele.bounding_box[1][0]) { bbox_brd[proj_idx][1][0] = ele.bounding_box[1][0]; }
      if (bbox_brd[proj_idx][1][1] < ele.bounding_box[1][1]) { bbox_brd[proj_idx][1][1] = ele.bounding_box[1][1]; }

    }

  }

  // delta position change of schematic and board elements to be placed
  //
  var _d = {
    "sch" : { "x" : 2*(bbox_sch[1][0] - bbox_sch[0][0]), "y": 2*(bbox_sch[1][1] - bbox_sch[1][0])  },
    "brd" : { "x" : 2*(bbox_brd[1][0] - bbox_brd[0][0]), "y": 2*(bbox_brd[1][1] - bbox_brd[1][1])  }
  };

  // rewire nets
  //

  var net_xfer = { "sch_newnet" : -10000, "sch_maxnet": -1, "sch" : {},
                   "brd_newnet" : -10000, "brd_maxnet": -1, "brd" : {} };
  /*
  var proj_idx = 1;
  var _p = proj[proj_idx];
  var _sch = _p.json_sch;
  var _brd = _p.json_brd;
  */

  // find max
  //var max_sch_net = -1;
  for (var proj_idx=0; proj_idx < proj.length; proj_idx++) {
    var _p = proj[proj_idx];
    var _sch = _p.json_sch;

    for (var ele_idx=0; ele_idx < _sch.element.length; ele_idx++) {
      var ele = _sch.element[ele_idx];
      if (!("pinData" in ele)) { continue; }

      for (var pin_key in ele["pinData"]) {
        if (!("netcode" in ele["pinData"][pin_key])) { continue; }

        var nc = parseInt(ele["pinData"][pin_key]["netcode"]);
        //if (max_sch_net < nc) { max_sch_net = nc; }
        if (net_xfer.sch_maxnet < nc) { net_xfer.sch_maxnet = nc; }
      }

    }
  }

  // use max as basis for new net mapping
  //
  //net_xfer.sch_newnet = max_sch_net + 1;
  net_xfer.sch_newnet = parseInt(net_xfer.sch_maxnet) + 1;

  // net_name_map : str netname -> int netcode
  // net_code_map : str netcode -> str netname
  // equipot : array of obj { net_name, net_number }
  // element : array of obj { netcode|net_number, .pad{ netcode|net_number } }
  //
  //var max_brd_net = -1;
  for (var proj_idx=0; proj_idx<proj.length; proj_idx++) {
    var _p = proj[proj_idx];
    var _brd = _p.json_brd;

    if ("equipot" in _brd) {
      for (var eqp_idx=0; eqp_idx<_brd.equipot.length; eqp_idx++) {
        var _equipot = _brd.equipot[eqp_idx];
        if ("net_number" in _equipot) {
          var nc = parseInt(_equipot["net_number"]);
          if (net_xfer.brd_maxnet < nc) { net_xfer.brd_maxnet = nc; }
        }
      }
    }

    if ("net_name_map" in _brd) {
      for (var _key in _brd.net_name_map) {
        var nc = parseInt(_brd.net_name_map[_key]);
        if (net_xfer.brd_maxnet < nc) { net_xfer.brd_maxnet = nc; }
      }
    }

    if ("net_code_map" in _brd) {
      for (var _nc in _brd.net_code_map) {
        if (!(_nc  in net_xfer.brd)) {
          var nc = parseInt(_nc);
          if (net_xfer.brd_maxnet < nc) { net_xfer.brd_maxnet = nc; }
        }
      }
    }

    for (var ele_idx=0; ele_idx < _brd.element.length; ele_idx++) {
      var ele = _brd.element[ele_idx];
      if ("netcode" in ele) {
        var nc = parseInt(ele["netcode"]);
        //if (max_brd_net < nc) { max_brd_net = nc; }
        if (net_xfer.brd_maxnet < nc) { net_xfer.brd_maxnet = nc; }
      }

      if ("net_number" in ele) {
        var nc = parseInt(ele["net_number"]);
        //if (max_brd_net < nc) { max_brd_net = nc; }
        if (net_xfer.brd_maxnet < nc) { net_xfer.brd_maxnet = nc; }
      }

      if (!("pad" in ele)) { continue; }
      for (var pad_idx=0; pad_idx < ele["pad"].length; pad_idx++) {
        var _pad = ele["pad"][pad_idx];
        if (!("net_number" in _pad)) { continue; }
        var nc = parseInt(_pad["net_number"]);
        //if (max_brd_net < nc) { max_brd_net = nc; }
        if (net_xfer.brd_maxnet < nc) { net_xfer.brd_maxnet = nc; }
      }


    }
  }

  //net_xfer.brd_newnet = max_brd_net + 1;
  net_xfer.brd_newnet = parseInt(net_xfer.brd_maxnet) + 1;


  // Now that we have a maximum and a base for the new
  // net assignmetns, go through and re-assign in the last project
  //

  var proj_idx = 1;
  var _p = proj[proj_idx];
  var _sch = _p.json_sch;
  var _brd = _p.json_brd;
  //proj_idx = 1;
  //_p = proj[proj_idx];
  //_sch = _p.json_sch;
  //_brd = _p.json_brd;


  // Go through each net and set up mapping information.
  // First for the schematic.
  //

  for (var ele_idx=0; ele_idx < _sch.element.length; ele_idx++) {
    var ele = _sch.element[ele_idx];
    if (!("pinData" in ele)) { continue; }

    for (var pin_key in ele["pinData"]) {
      if (!("netcode" in ele["pinData"][pin_key])) { continue; }

      var nc = ele["pinData"][pin_key]["netcode"];
      if (nc in net_xfer.sch) { continue; }
      net_xfer.sch[nc] = {
        "orig" : nc,
        "new" : net_xfer.sch_newnet
      };

      net_xfer.sch_newnet++;
    }

  }

  // now set up mapping for brd
  //

  for (var ele_idx=0; ele_idx < _brd.element.length; ele_idx++) {
    var ele = _brd.element[ele_idx];

    if ("netcode" in ele) {
      var nc = ele["netcode"];
      if (!(nc in net_xfer.brd)) {
        net_xfer.brd[nc] = {
          "orig": nc,
          "new" : net_xfer.brd_newnet
        };
        net_xfer.brd_newnet++;
      }
    }
    else if ("net_number" in ele) {
      var nc = ele["net_number"];
      if (!(nc in net_xfer.brd)) {
        net_xfer.brd[nc] = {
          "orig": nc,
          "new" : net_xfer.brd_newnet
        };
        net_xfer.brd_newnet++;
      }
    }
  }

  if ("equipot" in _brd) {
    for (var eqp_idx=0; eqp_idx<_brd.equipot.length; eqp_idx++) {
      var _equipot = _brd.equipot[eqp_idx];
      if ("net_number" in _equipot) {
        var nc = _equipot["net_number"];
        net_xfer.brd[nc] = {
          "orig": nc,
          "new" : net_xfer.brd_newnet
        };
        net_xfer.brd_newnet++;
      }
    }
  }

  if ("net_name_map" in _brd) {
    for (var _key in _brd.net_name_map) {
      var nc = _brd.net_name_map[_key];
      if (!(nc in net_xfer.brd)) {
        net_xfer.brd[nc] = {
          "orig": nc,
          "new" : net_xfer.brd_newnet
        };
        net_xfer.brd_newnet++;
      }
    }
  }

  if ("net_code_map" in _brd) {
    for (var nc in _brd.net_code_map) {
      if (!(nc  in net_xfer.brd)) {
        net_xfer.brd[nc] = {
          "orig": nc,
          "new" : net_xfer.brd_newnet
        };
        net_xfer.brd_newnet++;
      }
    }
  }

  if ("pad" in ele) {

    for (var pad_idx=0; pad_idx < ele["pad"].length; pad_idx++) {
      var _pad = ele["pad"][pad_idx];
      if (!("net_number" in _pad)) { continue; }

      var nc = _pad["net_number"];
      if (nc in net_xfer.brd) { continue; }

      net_xfer.brd[nc] = {
        "orig": nc,
        "new" : net_xfer.brd_newnet
      };
      net_xfer.brd_newnet++;
    }

  }

  //DEBUG
  //console.log("net_xfer:", JSON.stringify(net_xfer, null, 2));

  // Once we have the data for the mapping, go through and perform
  // the mapping
  //

  // first the schematic
  //
  for (var ele_idx=0; ele_idx < _sch.element.length; ele_idx++) {
    var ele = _sch.element[ele_idx];
    if (!("pinData" in ele)) { continue; }

    for (var pin_key in ele["pinData"]) {
      if (!("netcode" in ele["pinData"][pin_key])) { continue; }
      var nc = ele["pinData"][pin_key]["netcode"];
      ele["pinData"][pin_key]["netcode"] = net_xfer.sch[nc]["new"];
    }
  }

  for (var ele_key in _sch.net_pin_id_map) {
    var ele = _sch.net_pin_id_map[ele_key];
    var orig_nc = ele["netcode"];
    ele["netcode"] = net_xfer.sch[orig_nc]["new"];
  }

  // Then the board.
  // First the elements in the board.
  //
  for (var ele_idx=0; ele_idx < _brd.element.length; ele_idx++) {
    var ele = _brd.element[ele_idx];
    if ("netcode" in ele) {
      var orig_nc = ele["netcode"];
      ele["netcode"] = net_xfer.brd[orig_nc]["new"];
    }
    else if ("net_number" in ele) {
      var orig_nc = ele["netcode"];
      ele["net_number"] = net_xfer.brd[orig_nc]["new"];
    }

    if ("pad" in ele) {
      for (var pad_idx=0; pad_idx < ele["pad"].length; pad_idx++) {
        var pad = ele["pad"][pad_idx];

        if ("net_number" in pad) {
          var orig_nc = pad["net_number"];
          pad["net_number"] = net_xfer.brd[orig_nc]["new"];
        }
        else if ("netcode" in pad) {
          var orig_nc = pad["netcode"];
          pad["netcode"] = net_xfer.brd[orig_nc]["new"];
        }

      }
    }

  }

  // brd.equipot
  //
  if ("equipot" in _brd) {
    for (var eqp_idx=0; eqp_idx < _brd.equipot.length; eqp_idx++) {
      var equipot = _brd.equipot[eqp_idx];
      if (equipot["net_number"] == 0) { continue; }
      if (equipot["net_name"] == "") { continue; }
      var orig_nc = equipot["net_number"];
      equipot["net_number"] = net_xfer.brd[orig_nc]["new"];
      equipot["net_name"] = pretty_netname( equipot["net_number"] );
    }
  }

  if ("net_name_map" in _brd) {
    var del_key = [];
    for (var _key in _brd["net_name_map"]) {
      del_key.push(_key);
      var orig_nc = _brd["net_name_map"][_key];

      var new_nc = net_xfer.brd[orig_nc]["new"];
      var new_nc_name = pretty_netname( new_nc );

      _brd["net_name_map"][new_nc_name] = new_nc;
    }

    for (var ii=0; ii<del_key.length; ii++) {
      delete _brd["net_name_map"][del_key[ii]];
    }
  }

  if ("net_code_map" in _brd) {
    var del_key = [];
    for (var _key in _brd["net_code_map"]) {
      del_key.push(_key);
      var orig_nc = parseInt(_key);
      var new_nc_name = pretty_netname( new_nc );

      _brd["net_code_map"][new_nc] = new_nc_name;
    }
  }


  if ("sch_to_brd_net_map" in _brd) {
    var del_key = [];
    var s2b_netmap = _brd["sch_to_brd_net_map"];
    for (var _key in s2b_netmap) {
      del_key.push(_key);
      var sch_orig_nc = parseInt(_key);

      var sch_new_nc = net_xfer.sch[sch_orig_nc]["new"];

      s2b_netmap[sch_new_nc] = [];

      for (var ii=0; ii < s2b_netmap[_key].length; ii++) {
        var brd_orig_nc = s2b_netmap[_key][ii];
        var brd_new_nc = net_xfer.brd[brd_orig_nc]["new"];
        s2b_netmap[sch_new_nc].push(brd_new_nc);
      }
    }

    for (var ii=0; ii<del_key.length; ii++) {
      delete s2b_netmap[del_key[ii]];
    }
  }

  if ("brd_to_sch_net_map" in _brd) {
    var del_key = [];
    var b2s_netmap = _brd["brd_to_sch_net_map"];
    for (var _key in b2s_netmap) {
      del_key.push(_key);
      var brd_orig_nc = parseInt(_key);
      var brd_new_nc = net_xfer.brd[brd_orig_nc]["new"];
      
      b2s_netmap[brd_new_nc] = [];
      for (var ii=0; ii < b2s_netmap[_key].length; ii++) {
        var sch_orig_nc = b2s_netmap[_key][ii];
        var sch_new_nc = net_xfer.sch[sch_orig_nc]["new"];
        b2s_netmap[brd_new_nc].push(sch_new_nc);
      }
    }

    for (var ii=0; ii<del_key.length; ii++) {
      delete b2s_netmap[del_key[ii]];
    }
  }

  if ("sch_pin_id_net_map" in _brd) {
    var sch_pinmap = _brd["sch_pin_id_net_map"];
    for (var _key in sch_pinmap) {
      var sch_orig_nc = sch_pinmap[_key]["netcode"];
      var sch_new_nc = net_xfer.sch[sch_orig_nc]["new"];
      sch_pinmap[_key]["netcode"] = sch_new_nc;
    }
  }

  // Now that we have an updated projb, merge projb into proja and return
  //

  var sch_dst = proj[0].json_sch;
  var brd_dst = proj[0].json_brd;

  var sch_src = _sch;
  var brd_src = _brd;

  if (!("component_lib" in sch_dst)) { sch_dst["component_lib"] = {}; }
  if ("component_lib" in sch_src) {
    for (var _comp_name in sch_src.component_lib) {
      var _new_comp_name = _comp_name;
      if (_comp_name in sch_dst) {
        _new_comp_name = _comp_name + ":" + guid();
      }
      sch_dst.component_lib[_new_comp_name] = sch_src.component_lib[_comp_name];
    }
  }

  if (!("net_pin_id_map" in sch_dst)) { sch_dst["net_pin_id_map"] = {}; }
  if ("net_pin_id_map" in sch_src) {
    for (var _key in sch_src["net_pin_id_map"]) {
      sch_dst["net_pin_id_map"][_key] = sch_src["net_pin_id_map"][_key];
    }
  }

  if (!("element" in sch_dst)) { sch_dst["element"] = []; }
  if ("element" in sch_src) {
    for (var ii=0; ii<sch_src.element.length; ii++) {
      sch_dst.element.push( sch_src.element[ii] );
    }
  }

  //---

  if (!("equipot" in brd_dst)) { brd_dst["equipot"] = []; }
  if ("equipot" in brd_src) {
    for (var ii=0; ii<brd_src.equipot.length; ii++) {
      if (brd_src.equipot[ii]["net_name"] == "") { continue; }
      if (brd_src.equipot[ii]["net_number"] == 0) { continue; }
      brd_dst.equipot.push( brd_src.equipot[ii] );
    }
  }

  if (!("net_name_map" in brd_dst)) { brd_dst["net_name_map"] = {}; }
  if ("net_name_map" in brd_src) {
    for (var _key in brd_src.net_name_map) {
      if (_key == "") { continue; }
      if (brd_src.net_name_map[_key] == 0) { continue; }
      brd_dst.net_name_map[ _key ] = brd_src.net_name_map[ _key ];
    }
  }

  if (!("net_code_map" in brd_dst)) { brd_dst["net_code_map"] = {}; }
  if ("net_code_map" in brd_src) {
    for (var _key in brd_src.net_code_map) {
      if (_key == "0") { continue; }
      if (brd_src.net_code_map[_key] == "") { continue; }
      brd_dst.net_code_map[ _key ] = brd_src.net_code_map[ _key ];
    }
  }

  if (!("element" in brd_dst)) { brd_dst["element"] = []; }
  if ("element" in brd_src) {
    for (var ii=0; ii<brd_src.element.length; ii++) {
      brd_dst.element.push( brd_src.element[ii] );
    }
  }

  if (!("sch_to_brd_net_map" in brd_dst)) { brd_dst["sch_to_brd_net_map"] = {}; }
  if ("sch_to_brd_net_map" in brd_src) {
    for (var _key in brd_src["sch_to_brd_net_map"]) {
      brd_dst["sch_to_brd_net_map"][_key] = brd_src["sch_to_brd_net_map"][_key];
    }
  }

  if (!("brd_to_sch_net_map" in brd_dst)) { brd_dst["brd_to_sch_net_map"] = {}; }
  if ("brd_to_sch_net_map" in brd_src) {
    for (var _key in brd_src["brd_to_sch_net_map"]) {
      brd_dst["brd_to_sch_net_map"][_key] = brd_src["brd_to_sch_net_map"][_key];
    }
  }

  if (!("sch_pin_id_net_map" in brd_dst)) { brd_dst["sch_pin_id_net_map"] = {}; }
  if ("sch_pin_id_net_map" in brd_src) {
    for (var _key in brd_src["sch_pin_id_net_map"]) {
      brd_dst["sch_pin_id_net_map"][_key] = brd_src["sch_pin_id_net_map"][_key];
    }
  }


  if (!("footprint_lib" in brd_dst)) { brd_dst["footprint_lib"] = {}; }
  if ("footprint_lib" in brd_src) {
    for (var _key in brd_src["footprint_lib"]) {
      var _dst_key = _key;
      if (_key in brd_dst["footprint_lib"]) { _dst_key = _key + ":" + guid(); }
      brd_dst["footprint_lib"][_dst_key] = brd_src["footprint_lib"][_key];
    }
  }

  return proj[0];
}

module.exports = {
  "join" : _join_sch_brd,
  "merge" : _merge_project
};
