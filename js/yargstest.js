var yargv = require("yargs").argv;

if (yargv.x) {
  console.log("x", yargv.x, typeof yargv.x );
}

if (yargv.y) {
  console.log("y", yargv.y, typeof yargv.y);
}


