package main

import "fmt"
import "github.com/kataras/iris"
import _ "github.com/kataras/iris/utils"

import "io/ioutil"


func (ce *CustomEngine) Response(val interface{}, options ...map[string]interface{}) ([]byte, error) {
  dat := val.([]byte)

  fmt.Printf("mewpng response: render (%d)\n", len(dat))

  return dat, nil
}

func MewPNG(ctx *iris.Context) {

  ri := RenderInfo{ DBClient: g_redis_cli, LoggedIn:false, UserName:"", SessionToken:"", Anonymous:false, LandingPage:true, Footer:"", Analytics:"" }

  userid := ctx.GetCookie("userId") ; _ = userid
  sessionid := ctx.GetCookie("sessionId") ; _ = sessionid
  ri.UpdateSession(userid, sessionid)

  rest_projectid := string(ctx.Param("projectId"))
  form_projectid := string(ctx.FormValue("projectId"))

  fmt.Printf("  projectid (%v %v)\n", rest_projectid, form_projectid)

  projectid := form_projectid
  if rest_projectid != "" { projectid = rest_projectid }

  rest_fn := string(ctx.Param("f"))
  form_fn := string(ctx.FormValue("f"))
  inp_fn := form_fn
  if rest_fn != "" { inp_fn = rest_fn }

  owner_userid := ProjectUserId(g_redis_cli, projectid)

  authorized := false

  //DEBUG
  fmt.Printf("MewPNG: userid: %s, owner_userid %s\n", userid, owner_userid)
  fmt.Printf("MewPNG: rest_projectid: %s, form_projectid %s\n", rest_projectid, form_projectid)

  if owner_userid != userid {
    perm := ProjectPerm(g_redis_cli, projectid)

    //DEBUG
    fmt.Printf("  not owner: perm %s\n", perm)

    if perm == "world-read" { authorized = true }
  } else {

    //DEBUG
    fmt.Printf("  owner (authorized)\n")

    authorized = true
  }


  if !authorized {

    // error, show a default png that represents
    // the png wasn't found.
    //
    err_png := "img/ghost_alt_big.png"
    dat, err := ioutil.ReadFile(err_png)
    if err!=nil {
      fmt.Printf("mewpng: error (1) %v (%s)\n", err, err_png)
      ctx.Render("error.html", nil)
      return
    }

    fmt.Printf("mewpng: render (%d)\n", len(dat))

    ctx.MustRender("image/png", dat)
    return
  }

  var err error

  fn,e := FileCascadeFn(owner_userid, projectid, inp_fn)
  if e!=nil {

    fmt.Printf("file cascade error: %v (owner_userid %s, projectid %s, inp_fn %s)\n", e, owner_userid, projectid, inp_fn)

    err_png := "img/ghost_alt_big.png"
    dat, err := ioutil.ReadFile(err_png)
    if err!=nil {
      fmt.Printf("mewpng: error (1) %v (%s)\n", err, err_png)
      ctx.Render("error.html", nil)
      return
    }

    ctx.MustRender("image/png", dat)
    return
  }

  //DEBUG
  fmt.Printf("  mewpng: fn %sn", fn)

  dat, err := ioutil.ReadFile(fn)
  if err!=nil {

    fmt.Printf("mewpng: error %v (%s)\n", err, fn)

    ctx.Render("error.html", nil)
    return
  }

  fmt.Printf("mewpng: render (%d)\n", len(dat))

  ctx.MustRender("image/png", dat)
  return
}

func picmodlib(ctx *iris.Context) {
  dat, err := ioutil.ReadFile("img/ghost_alt_big.png")
  if err!=nil {

    fmt.Printf("picmodlib: error %v\n", err)

    ctx.Render("error.html", nil)
    return
  }

  fmt.Printf("picmodlib: render (%d)\n", len(dat))

  //ctx.Render("image/png", dat)
  ctx.MustRender("image/png", dat)
  return
}
