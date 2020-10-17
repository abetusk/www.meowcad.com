package main

//import "os"
import "fmt"
import _ "strings"

//import "github.com/iris-contrib/sessiondb/redis"
//import "github.com/iris-contrib/sessiondb/redis/service"

import "gopkg.in/redis.v4"
//import "github.com/go-redis/redis"

import "github.com/kataras/iris"
import _ "github.com/kataras/iris/utils"

import "github.com/valyala/fasthttp"

import "crypto/sha512"
import "encoding/hex"

import "encoding/json"
import "io/ioutil"


var g_redis_cli *redis.Client

var BASE_HOST string = "https://localhost"

type CustomEngine struct{}

type ProjectInfo struct {
  Id string
  Owner string
  Name string
  Sch string
  Brd string
  SchPicId string
  BrdPicId string
  Perm string
}

type CircuitElement struct {
  Data string `json:"data"`
  Name string `json:"name"`
  Id string `json:"id"`
  Type string `json:"type"`
  List []CircuitElement `json:"list"`
}


type RenderInfo struct {
  LoggedIn bool
  Anonymous bool
  LandingPage bool

  UserId string
  UserName string
  SessionToken string
  Project []ProjectInfo

  CurProject ProjectInfo

  ModuleList []CircuitElement
  ComponentList []CircuitElement

  Footer string
  Analytics string

  MessageNominal bool
  MessageError bool
  MessageWarning bool
  MessageInfo bool
  MessageSuccess bool
  MessageDanger bool
  MessagePrimary bool
  Message string

  PortfolioAdminPermission bool
  ProjectAdminPermission bool

  Title string

  DBClient *redis.Client
}

func (ri *RenderInfo) LoadCircuitElements() {
  module_json_fn := "json/footprint_list_default.json"
  component_json_fn := "json/component_list_default.json"

  mod_bytes,err := ioutil.ReadFile(module_json_fn)
  if err!=nil {
    fmt.Printf("%v\n", err)
    return
  }

  e := json.Unmarshal(mod_bytes, &(ri.ModuleList))
  if e!=nil { return }

  com_bytes,err := ioutil.ReadFile(component_json_fn)
  if err!=nil {
    fmt.Printf("%v\n", err)
    return
  }

  e = json.Unmarshal(com_bytes, &(ri.ComponentList))
  if e!=nil { return }

}

func (ri *RenderInfo) UpdateSession(userid, sessionid string) {

  if (userid != "") && (sessionid != "") {
    b := sha512.Sum512( []byte(userid + sessionid) )
    hashsessionid := hex.EncodeToString(b[:])

    z := ri.DBClient.SIsMember("sesspool", hashsessionid)
    if z.Val() {
      z1 := ri.DBClient.HGetAll("user:" + userid)
      m,e := z1.Result()
      if e!=nil { return }

      if m["active"] != "1" {
        ri.LoggedIn = false
        return
      }

      ri.LoggedIn = true
      ri.UserId = userid

      if m["type"] == "user" {
        ri.UserName = m["userName"]
      } else {
        ri.Anonymous = true
      }

    } else {
      ri.LoggedIn = false
    }

  }

}

func RenderInfoCreate(ctx *iris.Context) RenderInfo {
  ri := RenderInfo{ DBClient: g_redis_cli, LoggedIn:false, UserName:"", SessionToken:"", Anonymous:false, LandingPage:true, Footer:"", Analytics:"" }

  userid := ctx.GetCookie("userId") ; _ = userid
  sessionid := ctx.GetCookie("sessionId") ; _ = sessionid
  ri.UpdateSession(userid, sessionid)

  msg := ctx.GetCookie("message") ; _ = msg
  msgtype := ctx.GetCookie("messageType") ; _ = msgtype
  if msgtype == "" {
  } else {
    ri.Message = msg
    if msgtype == "success" {
      ri.MessageSuccess = true
    } else if msgtype == "error" {
      ri.MessageError = true
    } else if (msgtype == "status") || (msgtype == "info") {
      ri.MessageInfo = true
    }
  }

  ctx.RemoveCookie("message")
  ctx.RemoveCookie("messageType")

  return ri
}

func RenderInfoUserSession(userid, sessionid string) RenderInfo {
  ri := RenderInfo{ DBClient: g_redis_cli, LoggedIn:false, UserName:"", SessionToken:"", Anonymous:false, LandingPage:true, Footer:"", Analytics:"" }
  ri.UpdateSession(userid, sessionid)
  return ri
}

func login(ctx *iris.Context) {
  ri := RenderInfoCreate(ctx)

  dst_page := "login.html"
  if ri.LoggedIn { dst_page = "portfolio.html" }

  e := ctx.Render(dst_page, ri)
  if e!=nil { fmt.Printf("login error: %v\n", e) }

}

func forgot(ctx *iris.Context) {
  ri := RenderInfoCreate(ctx)

  dst_page := "forgot.html"
  if ri.LoggedIn { dst_page = "portfolio.html" }

  e := ctx.Render(dst_page, ri)
  if e!=nil { fmt.Printf("forgot error: %v\n", e) }

}

func project(ctx *iris.Context) {
  var ok bool
  ri := RenderInfoCreate(ctx)

  dst_page := "project.html"

  ri.LoadCircuitElements()

  userid := ctx.GetCookie("userId")

  rest_project_id := ctx.Param("project_id")
  form_project_id := ctx.FormValue("projectId")

  projectid := string(form_project_id)
  if rest_project_id != "" { projectid = string(rest_project_id) }

  _ = userid
  _ = rest_project_id
  _ = form_project_id

  ri.CurProject,ok = GetProject(g_redis_cli, userid, projectid)

  if !ok {
    fmt.Printf("project not found or unavailable: userid:%v projectid:%v\n", userid, projectid)
    ri.Title = "Not Found"
    ri.Message = "..."
    dst_page = "sink.html"
  } else {

    // Simple permissions for now.  If your'e the owner, you can
    // edit it.
    //
    ri.ProjectAdminPermission = false
    if ri.CurProject.Owner == ri.UserId {
      ri.ProjectAdminPermission = true
    }

  }

  e := ctx.Render(dst_page, ri)
  if e!=nil { fmt.Printf("project error: %v\n", e) }
}

func portfolio(ctx *iris.Context) {
  ri := RenderInfoCreate(ctx)

  ri.LoadCircuitElements()

  userid := ctx.GetCookie("userId")

  rest_user_id := ctx.Param("userid")
  form_user_id := ctx.FormValue("userId")

  view_user_id := string(rest_user_id)
  if len(form_user_id)>0 {
    view_user_id = string(form_user_id)
  } else {
    view_user_id = string(userid)
  }
  _ = view_user_id

  sessionid := ctx.GetCookie("sessionId")

  p,ok := GetPortfolio(g_redis_cli, userid, sessionid, view_user_id)
  if !ok { fmt.Printf("error: %v\n", ok) }
  _ = p

  ri.Project = p

  ri.PortfolioAdminPermission = false
  if view_user_id == userid {
    ri.PortfolioAdminPermission = true
  }

  e := ctx.Render("portfolio.html", ri)
  if e!=nil { fmt.Printf("portfolio error: %v\n", e) }
}

func user(ctx *iris.Context) {
  ri := RenderInfoCreate(ctx)

  e := ctx.Render("user.html", ri)
  if e!=nil { fmt.Printf("usererror: %v\n", e) }
  fmt.Printf("user... %v\n", ri)
}

func deleteproject(ctx *iris.Context) {
  ri := RenderInfoCreate(ctx) ; _ = ri

  fmt.Printf("deleteproject:...\n")

  projectid := ctx.FormValue("projectId")

  if (!ri.LoggedIn) || ri.Anonymous {
    ctx.SetCookieKV("message", "You do not have permissino to delete this project")
    ctx.SetCookieKV("messageType", "error")

    if ri.Anonymous || ri.LoggedIn {
      ctx.Redirect( BASE_HOST + "/portfolio")
    } else {
      ctx.Redirect( BASE_HOST + "/landing")
    }
    return
  }

  var ok bool
  ri.CurProject,ok = GetProject(g_redis_cli, ri.UserId, string(projectid))

  fmt.Printf(">>> userid %s, projectid %s (%s)\n", ri.UserId, projectid, ri.CurProject.Id)

  if !ok {
    fmt.Printf("project not found or unavailable: userid:%v projectid:%v\n", ri.UserId, projectid)
    ri.Title = "Not Found"
    ri.Message = "Project not found"
    e := ctx.Render("sink.html", ri)
    if e!=nil { fmt.Printf("project error: %v\n", e) }
    return

  } else {

    // Simple permissions for now.  If your'e the owner, you can
    // edit it.
    //
    if ri.CurProject.Owner != ri.UserId {
      ctx.SetCookieKV("message", "You do not have permissino to delete this project")
      ctx.SetCookieKV("messageType", "error")
      ctx.Redirect( BASE_HOST + "/portfolio")
      return
    }
    ri.ProjectAdminPermission = true

    DeleteProject(g_redis_cli, string(projectid))

  }

  ctx.SetCookieKV("message", "Project deleted")
  ctx.SetCookieKV("messageType", "warning")

  ctx.Redirect( BASE_HOST + "/portfolio" )
}

func createproject(ctx *iris.Context) {
  ri := RenderInfoCreate(ctx) ; _ = ri

  if (!ri.LoggedIn) || ri.Anonymous {
    ctx.SetCookieKV("message", "You do not have permission to create a new project")
    ctx.SetCookieKV("messageType", "error")

    if ri.Anonymous || ri.LoggedIn {
      ctx.Redirect( BASE_HOST + "/portfolio")
    } else {
      ctx.Redirect( BASE_HOST + "/landing")
    }
    return
  }

  proj_name := ctx.FormValue("name")
  perm := ctx.FormValue("permissionOption")

  fmt.Printf("createproject: %s %s\n", proj_name, perm)

  if len(proj_name) == 0 {
    ctx.SetCookieKV("message", "Project name must be non-empty")
    ctx.SetCookieKV("messageType", "error")
    ctx.Redirect( BASE_HOST + "/portfolio")
    return
  }

  proj_perm := "user"
  if string(perm) != "private" { proj_perm = "world-read" }
  CreateProject(g_redis_cli, []byte(ri.UserId), proj_name, []byte(proj_perm))

  ctx.Redirect( BASE_HOST + "/portfolio" )
}

func user_post(ctx *iris.Context) {
  ri := RenderInfoCreate(ctx) ; _ = ri

  password_old := ctx.FormValue("passwordOrig")
  password_new := ctx.FormValue("password")
  password_confirm := ctx.FormValue("passwordAgain")

  if ok,msg := ValidPassword(string(password_new)) ; !ok {
    ctx.SetCookieKV("message", msg)
    ctx.SetCookieKV("messageType", "error")

    ctx.Redirect( BASE_HOST + "/user")
    return
  }

  if string(password_new) != string(password_confirm) {
    ctx.SetCookieKV("message", "Passwords do not match")
    ctx.SetCookieKV("messageType", "error")
    ctx.Redirect( BASE_HOST + "/user")
    return
  }

  userid := ctx.GetCookie("userId")

  if !AuthenticateUser(g_redis_cli, string(userid), string(password_old)) {
    ctx.SetCookieKV("message", "Authentication failure")
    ctx.SetCookieKV("messageType", "error")
    ctx.Redirect( BASE_HOST + "/user")
    return
  }

  ChangePassword(g_redis_cli, string(userid), string(password_new))

  ctx.SetCookieKV("message", "Password changed!")
  ctx.SetCookieKV("messageType", "success")
  ctx.Redirect( BASE_HOST + "/user")
}

func logout(ctx *iris.Context) {
  ri := RenderInfoCreate(ctx)

  if ri.LoggedIn {
    userid := ctx.GetCookie("userId")
    sessionid := ctx.GetCookie("sessionId")
    ctx.RemoveCookie("userId")
    ctx.RemoveCookie("sessionId")
    ctx.RemoveCookie("userName")

    b := sha512.Sum512( []byte(userid + sessionid) )
    hashsessionid := hex.EncodeToString(b[:])

    ri.DBClient.SRem( "sesspool", hashsessionid )
  }

  ctx.Redirect( BASE_HOST + "/")
}


func register(ctx *iris.Context) {
  ri := RenderInfoCreate(ctx)

  if ri.LoggedIn && (!ri.Anonymous) {
    ctx.Redirect( BASE_HOST + "/portfolio")
    return
  }

  e := ctx.Render("register.html", ri)
  if e!=nil { fmt.Printf("register error: %v\n", e) }
  fmt.Printf("register... %v\n", ri)
}

func RemoveCookie(ctx *iris.Context, key string) {
  c := fasthttp.AcquireCookie()
  c.SetKey(key)
  c.SetExpire(fasthttp.CookieExpireDelete)
  c.SetSecure(true)
  ctx.SetCookie(c)
  fasthttp.ReleaseCookie(c)
}

func SetCookieSecureKV(ctx *iris.Context, key, val string) {
  c := fasthttp.AcquireCookie()
  c.SetKey(key)
  c.SetValue(val)
  c.SetSecure(true)
  ctx.SetCookie(c)
  fasthttp.ReleaseCookie(c)
}

func register_post(ctx *iris.Context) {
  ri := RenderInfoCreate(ctx)

  ctx.RemoveCookie("signup_focus")
  ctx.RemoveCookie("signup_username")
  ctx.RemoveCookie("signup_email")

  if ri.LoggedIn && (!ri.Anonymous) {
    ctx.Redirect( BASE_HOST + "/portfolio")
    return
  }

  // This state should only happen if we're logged in as
  // an anonymous user.  Clear cookies that hold session
  // info and redirect to `register` page.
  //
  if ctx.FormValueString("type") == "clear" {

    ctx.RemoveCookie("userId")
    ctx.RemoveCookie("sessionId")
    ctx.RemoveCookie("userName")
    ctx.RemoveCookie("recentProjectId")
    ctx.RemoveCookie("signup_username")

    ctx.SetCookieKV("message", "Anonymous session cleared!")
    ctx.SetCookieKV("messageType", "success")
    ctx.Redirect( BASE_HOST + "/register")
    return
  }

  username := ctx.FormValue("username")
  email := ctx.FormValue("email")
  password := ctx.FormValue("password")
  fmt.Printf("register_post (redirect) %s %s %s\n", username, email, password)

  // Take care of the simple case first
  //
  if (len(username) == 0) || (len(password)==0) {
    ctx.SetCookieKV("message", "Please provide a user name and password")
    ctx.SetCookieKV("messageType", "error")

    SetCookieSecureKV(ctx, "signup_focus", "username")
    SetCookieSecureKV(ctx, "signup_email", string(email))

    ctx.Redirect( BASE_HOST + "/register")
    return
  }

  // Lookup username to see if it already exists
  //
  scmd := ri.DBClient.HGet( "username:" + string(username), "id")
  if scmd.Val() != "" {
    ctx.SetCookieKV("message", "We're sorry, that username already exists!  Please try another username")
    ctx.SetCookieKV("messageType", "error")

    SetCookieSecureKV(ctx, "signup_focus", "username")
    SetCookieSecureKV(ctx, "signup_email", string(email))

    ctx.Redirect( BASE_HOST + "/register")
    return
  }

  if ok,msg := ValidPassword(string(password)) ; !ok {

    ctx.SetCookieKV("message", msg)
    ctx.SetCookieKV("messageType", "error")

    SetCookieSecureKV(ctx, "signup_focus", "password")
    SetCookieSecureKV(ctx, "signup_username", string(username))
    SetCookieSecureKV(ctx, "signup_email", string(email))

    ctx.Redirect( BASE_HOST + "/register")
    return
  }


  // Success!
  // If there is already a userid and sessionid (via
  // anonymous login), transfer ownership.
  // Otherwise, createa userid, sessionid and initial
  // project.
  //
  var userid string
  var sessionid string

  if ri.LoggedIn && ri.Anonymous {

    // Anonymous, used the pre-existing informaiton
    //
    userid = ctx.GetCookie("userid")
    sessionid = ctx.GetCookie("sessionid")
    TransferUser(g_redis_cli, []byte(userid), []byte(username), []byte(password), []byte(email))

  } else {

    projname := "Starter Project"
    perm := "world-read"

    // non-logged-in user, create user, create session
    //
    userid = CreateUser(g_redis_cli, username, password, email)
    sessionid = CreateSession(g_redis_cli, userid)
    CreateProject(g_redis_cli, []byte(userid), []byte(projname), []byte(perm))

  }

  SetCookieSecureKV(ctx, "userId", string(userid))
  SetCookieSecureKV(ctx, "sessionId", string(sessionid))
  SetCookieSecureKV(ctx, "userName", string(username))

  ctx.SetCookieKV("message", "Welcome!")
  ctx.SetCookieKV("messageType", "success")

  // Probably redundant but diligent about
  // cleaning up after ourselves.
  //
  ctx.RemoveCookie("signup_focus")
  ctx.RemoveCookie("signup_username")
  ctx.RemoveCookie("signup_email")

  //ctx.Redirect("/portfolio")
  ctx.Redirect( BASE_HOST + "/portfolio")
}

func search(ctx *iris.Context) {
  ri := RenderInfoCreate(ctx)

  param := ctx.Param("search") ; _ = param
  m := ctx.URLParams() ; _ = m

  e := ctx.Render("search.html", ri)
  if e!=nil {
    fmt.Printf("searcherror: %v\n", e)
  }

}

func feedback_post(ctx *iris.Context) {
  ri := RenderInfoCreate(ctx)

  userid := ctx.GetCookie("userId")
  email := ctx.FormValue("email")
  feedback := ctx.FormValue("feedback")

  SendFeedback(g_redis_cli, string(userid), string(email), string(feedback))

  if ri.LoggedIn {
    SetCookieSecureKV(ctx, "message", "Thank you!  Your feedback has been sent")
    SetCookieSecureKV(ctx, "messageType", "info")

    ctx.Redirect( BASE_HOST + "/portfolio")
  } else {
    ctx.Redirect( BASE_HOST + "/landing")
  }

}

func feedback(ctx *iris.Context) {
  ri := RenderInfoCreate(ctx)

  e := ctx.Render("feedback.html", ri)
  if e!=nil { fmt.Printf("feedback error: %v\n", e) }

  fmt.Printf("feedback... %v\n", ri)

}

func blog(ctx *iris.Context) {
  ri := RenderInfoCreate(ctx)

  blog_page_idx := ctx.Param("blog")

  e := ctx.Render("blog.html", ri)
  if e!=nil {
    fmt.Printf("blog error: %v\n", e)
  }

  fmt.Printf("blog... %v %v\n", ri, blog_page_idx)

}

func explore(ctx *iris.Context) {
  ri := RenderInfoCreate(ctx)

  e := ctx.Render("explore.html", ri)
  if e!=nil {
    fmt.Printf("explore error: %v\n", e)
  }

}

func about(ctx *iris.Context) {
  ri := RenderInfoCreate(ctx)

  e := ctx.Render("about.html", ri)
  if e!=nil {
    fmt.Printf("about error: %v\n", e)
  }

}

func landing(ctx *iris.Context) {
  ri := RenderInfoCreate(ctx)

  if ri.LoggedIn {
    ctx.Redirect( BASE_HOST + "/portfolio")
    return
  }

  e := ctx.Render("landing.html", ri)
  if e!=nil {
    fmt.Printf("landing error: %v\n", e)
  }

}


func main() {

  g_redis_cli = redis.NewClient(&redis.Options{
    Addr:     "localhost:6379",
    Password: "", // no password set
    DB:       0,  // use default DB
  })
  pong, err := g_redis_cli.Ping().Result()
  fmt.Println(pong, err)

  iris.Get("/user", user)
  iris.Post("/user", user_post)

  iris.Get("/portfolio", portfolio)
  iris.Get("/portfolio/:userid", portfolio)
  iris.Get("/search", search)

  iris.Get("/project", project)
  iris.Get("/project/:projectid", project)

  iris.Post("/createproject", createproject)
  iris.Get("/deleteproject", deleteproject)
  iris.Post("/deleteproject", deleteproject)

  iris.Get("/login", login)
  iris.Get("/forgot", forgot)
  iris.Get("/logout", logout)
  iris.Get("/register", register)
  iris.Post("/register", register_post)

  iris.Get("/explore", explore)

  iris.Get("/feedback", feedback)
  iris.Post("/feedback", feedback_post)

  iris.Get("/about", about)
  iris.Get("/blog/:blog", blog)
  iris.Get("/blog", blog)

  iris.Get("/landing.html", landing)
  iris.Get("/landing.htm", landing)
  iris.Get("/landing", landing)

  iris.UseResponse(&CustomEngine{},  "image/png")
  iris.Get("/mewpng", MewPNG)

  //iris.Get("/picmodlib/:dir/:dirb/:dirc/:name", picmodlib)
  iris.Get("/picmodlib/*x", picmodlib)
  iris.Get("/picmodlib", picmodlib)

  iris.Get("/", landing)

  iris.StaticServe("./img", "/img")
  iris.StaticServe("./css", "/css")
  iris.StaticServe("./js", "/js")
  iris.StaticServe("./bootstrap", "/bootstrap")
  iris.StaticServe("./fonts", "/fonts")

  iris.Listen(":8085")
}

