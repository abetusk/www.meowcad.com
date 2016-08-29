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

/* 
 *
 * These are helper functions to aid in sending messages
 * across tabs.  Since we're on the same domain, cookies
 * are shared across the tabs.  We can use this as a low
 * bandwidth channel to communicate state between the two
 * tabs in question.
 *
 * The 'net highlight' feature uses these to communicate
 * mouse hover in one tab to indicate which net is highlighted
 * so the other tab can highlight them (from board to schematic,
 * for example)
 *
 */

var bleepsixTabCommunicationHeadless = false;
if ( typeof module !== 'undefined')
{
  bleepsixTabCommunicationHeadless = true;
  var bleepsixAux = require("../lib/meowaux.js");
  var guid = bleepsixAux.guid;
  var s4 = bleepsixAux.s4;
  var simplecopy = bleepsixAux.simplecopy;
}

function bleepsixTabCommunication()
{
  this.message = {};
  this.lastMessage = {};
}


/*
bleepsixTabCommunication.prototype.setId = function( id )
{
  this.id = id;
}
*/

bleepsixTabCommunication.prototype.addMessage = function( channelName, msg )
{

  localStorage.setItem( "meowmsg:" + channelName, msg );

  this.message[ channelName ] = msg;
  this.lastMessage[ channelName ] = "";

  return;

  if (this.id)
  {
    //$.cookie( "meowmsg:" + this.id, msg );
    localStorage.setItem( "meowmsg:" + this.id, msg );
  }
  else
  {
    console.log("WARNING: bleepsixTabCommunication.addMessage, id not set");
  }

}

bleepsixTabCommunication.prototype.hasNewMessage = function( channelName )
{
  var msg = localStorage.getItem( "meowmsg:" + channelName );
  return msg != this.lastMessage[ channelName ] ;
  this.message = localStorage.getItem( "meowmsg:" + this.id );
  return this.lastMessage != this.message ;
}

bleepsixTabCommunication.prototype.removeMessage = function( channelName, msg )
{

  $.removeCookie( "meowmsg:" + channelName, msg );
  this.message[ channelName ] = "";
  this.lastMessage[ channelName ] = "";
  return;


  if (this.id)
  {
    $.removeCookie( "meowmsg:" + this.id, msg );
    this.message = null;
    this.lastMessage = null;
  }
  else
  {
    console.log("WARNING: bleepsixTabCommunication.removeMessage, id not set");
  }

}

bleepsixTabCommunication.prototype.processMessage = function( channelName, msg )
{

  var x = localStorage.getItem( "meowmsg:" + channelName );
  this.lastMessage[ channelName ] = x;
  return x;


  if (this.id)
  {
    //var x = $.cookie( "meowmsg:" + this.id );
    var x = localStorage.getItem( "meowmsg:" + this.id );
    this.lastMessage = x;
    return x;
  }
  else
  {
    console.log("WARNING: bleepsixTabCommunication.processMessage, id not set");
  }


}

bleepsixTabCommunication.prototype.peekMessage = function( channelName )
{
  return localStorage.getItem( "meowmsg:" + channelName );



  if (this.id)
  {
    //return $.cookie( "meowmsg:" + this.id );
    return localStorage.getItem( "meowmsg:" + this.id );
  }
  else
  {
    console.log("WARNING: bleepsixTabCommunication.peekMesssage, id not set");
  }

}


