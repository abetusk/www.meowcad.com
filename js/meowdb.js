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

// Database (?) for MeowCAD
// NOT FUNCTIONING / IN DEVELOPMENT
//
var async = require("async");
var fs = require("fs");

function meowdb() {
  this.ok = true;
  this.data_dir = "meowdb";
}

// set add
//
meowdb.prototype.sadd( table, val ) {

  var _fn = this.data_dir + "/" + table;

  var _dat = fs.readFileSync( _fn, 'utf8');
  var _json = JSON.parse(_dat);

  if ( !("sadd" in _json) ) {
    _json["sadd"] = [];
  }
  _json.sadd.push(val);

  fs.writeFileSync( _fn, JSON.stringify(_json), 'UTF-8');

}

// hash map set
//
meowdb.prototype.hmset( table, val ) {

  var _fn = this.data_dir + "/hmset";

  var _dat = fs.readFileSync( _fn, 'utf8');
  var _json = JSON.parse(_dat);

  _json[table] = val;

  fs.writeFileSync( _fn, JSON.stringify(_json), 'UTF-8');
}


// array push
//
meowdb.prototype.rpush( table, val ) {
}

