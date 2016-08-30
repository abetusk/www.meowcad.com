package main

import "fmt"
import "time"
import "github.com/satori/go.uuid"
import "gopkg.in/redis.v4"

import "crypto/sha512"
import "encoding/hex"

import "strconv"
//import "strings"

import "io/ioutil"
import "strings"
import "path/filepath"
import "os"

func map2json(m map[string]string) string {
  a := []string{}
  for k,v := range m {
    a = append(a, fmt.Sprintf("%s:%s", strconv.QuoteToASCII(k), strconv.QuoteToASCII(v)))
  }
  return strings.Join(a, ",")
}

func ValidPassword(password string) (bool,string) {
  // Check password conditions (if less than 20 chars, needs mixed alphanumeric case).
  //
  n,ncap,nnum := 0,0,0
  for i:=0; i<len(password); i++ {
    n++
    if (password[i] >= 'A') && (password[i] <= 'Z') { ncap++ }
    if (password[i] >= '0') && (password[i] <= '9') { nnum++ }
  }
  if ((n<8) && ((ncap==0) || (ncap==n) || (nnum==0))) {
    return false, "Password less than 20 characters long must contain mixed case, at least one number and be at least 7 characters long"
  }

  return true,""
}

func GetPortfolio(cli *redis.Client, userid, sessionid, view_userid string) ([]ProjectInfo,bool) {
  b := sha512.Sum512( []byte(string(userid) + string(sessionid)) )
  hashsessionid := hex.EncodeToString(b[:])

  r := cli.HGetAll("session:" + hashsessionid)
  sess,e := r.Result()
  if e!=nil { return nil,false }

  if sess["active"] != "1" { return nil,false }

  r1 := cli.HGetAll("user:" + view_userid)
  view_user,e := r1.Result()
  if e!=nil { return nil,false }

  if view_user["active"] != "1" { return nil, false }

  r2 := cli.LLen("olio:" + view_userid)
  n_portfolio,e := r2.Result()
  if e!=nil { return nil,false }

  r3 := cli.LRange("olio:" + view_userid, 0, n_portfolio)
  portfolio,e := r3.Result()
  if e!=nil { return nil,false }

  proj_info := []ProjectInfo{}
  for i:=0; i<len(portfolio); i++ {
    rproj := cli.HGetAll("project:" + portfolio[i])
    proj,e := rproj.Result()
    if e!=nil { return nil,false }

    if (proj["userId"] != userid) && (proj["permission"] != "world-read") { continue }
    if proj["active"] != "1" { continue }

    schpic := ""
    brdpic := ""
    picinfo,e := cli.HGetAll("projectpic:" + proj["id"]).Result()

    if e==nil {
      schpic = picinfo["schPicId"]
      brdpic = picinfo["brdPicId"]
    }

    proj_info = append(proj_info, ProjectInfo{ Id:proj["id"], Owner:proj["userId"], Name:proj["name"], SchPicId:schpic, BrdPicId:brdpic })
  }

  return proj_info, true
}

func GetProject(cli *redis.Client, userid, projectid string) (ProjectInfo, bool) {
  proj,e := cli.HGetAll("project:" + projectid).Result()
  if e!=nil { return ProjectInfo{},false }
  if (proj["userId"] != userid) && (proj["permission"] != "world-read") { return ProjectInfo{}, false }

  schpic := ""
  brdpic := ""
  picinfo,e := cli.HGetAll("projectpic:" + projectid).Result()

  if e==nil {
    schpic = picinfo["schPicId"]
    brdpic = picinfo["brdPicId"]
  }

  return ProjectInfo{ Id:proj["id"], Owner:proj["userId"], Name:proj["name"], SchPicId:schpic, BrdPicId:brdpic, Perm:proj["permission"] },true
}

func ChangePassword(cli *redis.Client, userid, password string) bool {
  b := sha512.Sum512( []byte(string(userid) + string(password)) )
  hashpassword := hex.EncodeToString(b[:])

  cli.HSet("user:" + userid, "passwordHash", hashpassword)
  return true
}

func AuthenticateUser(cli *redis.Client, userid, password string) bool {
  b := sha512.Sum512( []byte(string(userid) + string(password)) )
  hashpassword := hex.EncodeToString(b[:])

  r := cli.HGetAll("user:" + string(userid))
  user,e := r.Result()
  if e!=nil { return false }

  if user["passwordHash"] == hashpassword { return true }
  return false
}

func DeactivateSession(cli *redis.Client, userid, sessionid string) {
  b := sha512.Sum512( []byte(userid + sessionid) )
  hashsessionid := hex.EncodeToString(b[:])

  cli.SRem("sesspool", hashsessionid)
  cli.HSet("session:" + hashsessionid, "active", "0")
}

func SendFeedback(cli *redis.Client, userid, email, feedback string) bool {
  u1 := uuid.NewV4()
  feedbackid := fmt.Sprintf("%s", u1)

  t := time.Now()
  tstr := fmt.Sprintf("%d", t.UnixNano())
  tstamp := fmt.Sprintf("%v", t)

  f := make(map[string]string)
  f["id"] = feedbackid
  f["text"] = string(feedback)
  f["email"] = string(email)
  f["stime"] = tstr
  f["timestamp"] = tstamp
  f["userId"] = string(userid)

  cli.HMSet("feedback:" + feedbackid, f)
  cli.SAdd("feedbackpool", feedbackid)

  return true
}

func CreateSession(cli *redis.Client, userid string) string {
  u1 := uuid.NewV4()
  sessionid := fmt.Sprintf("%s", u1)

  b := sha512.Sum512( []byte(userid + sessionid) )
  hashsessionid := hex.EncodeToString(b[:])

  cli.SAdd("sesspool", hashsessionid)

  sess := make(map[string]string)
  sess["id"] = hashsessionid
  sess["active"] = "1"
  sess["userId"] = userid
  cli.HMSet("session:" + hashsessionid, sess)

  return sessionid
}

func TransferUser(cli *redis.Client, userid, username, password, email []byte) bool {
  r := cli.HGetAll("user:" + string(userid))
  u,e := r.Result()
  if e != nil { return false }

  if u["type"] != "anonymous" { return false }

  b := sha512.Sum512( []byte(string(userid) + string(password)) )
  hashpassword := hex.EncodeToString(b[:])

  cli.HSet("user:" + string(userid), "userName", string(username))
  cli.HSet("user:" + string(userid), "passwordHash", string(hashpassword))
  cli.HSet("user:" + string(userid), "type", "user")
  cli.HSet("user:" + string(userid), "email", string(email))

  uh := make(map[string]string)
  uh["id"] = string(userid)
  uh["userName"] = string(username)
  cli.HMSet("username:" + string(username), uh)

  return true
}

func CreateUser(cli *redis.Client, username, password, email []byte) string {
  u1 := uuid.NewV4()
  userid := fmt.Sprintf("%s", u1)

  b := sha512.Sum512( []byte(string(userid) + string(password)) )
  hashpassword := hex.EncodeToString(b[:])

  u := make(map[string]string)
  u["id"] = userid
  u["userName"] = string(username)
  cli.HMSet("username:" + string(username), u)

  t := time.Now()
  tstr := fmt.Sprintf("%d", t.UnixNano())
  tstamp := fmt.Sprintf("%v", t)

  u = make(map[string]string)
  u["id"] = userid
  u["userName"] = string(username)
  u["passwordHash"] = hashpassword
  u["email"] = string(email)
  u["active"] = "1"
  u["type"] = "user"
  u["time"] = tstr
  u["timestamp"] = tstamp
  cli.HMSet("user:" + userid, u)

  cli.SAdd("userpool", userid)

  return userid
}

func ProjectUserId(cli *redis.Client, projectid string) string {
  u,e := cli.HGet("project:" + projectid, "userId").Result()
  if e!=nil { return "" }
  return u
}

func ProjectPerm(cli *redis.Client, projectid string) string {
  u,e := cli.HGet("project:" + projectid, "permission").Result()

  if e!=nil { return "owner" }
  return u
}

func CreateProject(cli *redis.Client, userid, projectName, permission []byte) {
  u1 := uuid.NewV4()
  projid := fmt.Sprintf("%s", u1)

  r := cli.HGetAll("user:" + string(userid))
  _,e := r.Result()
  if e!=nil { return }

  cli.RPush("olio:" + string(userid), projid)

  t := time.Now()
  tstr := fmt.Sprintf("%d", t.UnixNano())
  tstamp := fmt.Sprintf("%v", t)

  proj := make(map[string]string)
  proj["id"] = projid
  proj["userId"] = string(userid)
  proj["name"] = string(projectName)
  proj["active"] = "1"
  proj["stime"] = tstr
  proj["timestamp"] = tstamp
  if string(permission) == "world-read" {
    proj["permission"] = "world-read"
  } else {
    proj["permission"] = "user"
  }
  cli.HMSet("project:" + proj["id"], proj)

  default_net := `{"Default":{"name":"Default","description":"default net class","unit":"deci-thou",` +
    `"track_width":100,"clearance":100,"via_diameter":472,"via_drill_diameter":250,"uvia_diameter":200,"uvia_drill_diameter":50,"net":[]}}`

  json_sch := `{"element":[], "component_lib":{}, "net_pin_id_map":{} }`
  json_brd := `{"units":"deci-mils", "element":[], "equipot":[{"net_name":"", "net_number":0}], "net_class":` + default_net + `}`

  snap := make(map[string]string)
  snap["id"] = proj["id"]
  snap["json_sch"] = json_sch
  snap["json_brd"] = json_brd
  cli.HMSet("projectsnapshot:" + proj["id"], snap)

  u2 := uuid.NewV4()
  evid := fmt.Sprintf("%s", u2)

  evdata := make(map[string]string)
  evdata["json_sch"] = json_sch
  evdata["json_brd"] = json_brd
  evdata["type"] = "none"
  evdata["source"] = "none"
  evdata["destination"] = "none"
  evdata["action"] = "snaphost"

  ev := make(map[string]string)
  ev["data"] = map2json(evdata)

  cli.HMSet("projectop:" + evid, ev)
  cli.RPush("projectevent:" + proj["id"], evid)

  cli.HSet("projectrecent:" + string(userid), "projectId", proj["id"])
  cli.SAdd("projectpool", proj["id"])

}

func DeleteProject(cli *redis.Client, projectid string) {
  cli.HSet("project:" + projectid, "active", "0")
}

//var DEFAULT_DATA_LOCATION string = "/var/www/data"
//var DEFAULT_DATA_LOCATION string = "/home/abe/play/abetusk/mewgo/json"
var DEFAULT_DATA_LOCATION string = "./"
var USR_BASE_LOCATION     string = "/home/meow/usr"


func FileCascadeFn(userid, projectid, fn string) (string,error) {
  fullfn := ""

  if (userid!="") && (projectid!="") {
    usrDir := USR_BASE_LOCATION + "/" + userid
    projDir := usrDir + "/" + projectid

    if inDirectory(usrDir, USR_BASE_LOCATION) {

      if inDirectory(projDir, usrDir) {
        fullfn = projDir + "/" + fn

        if inDirectory(fullfn, projDir) {
          if _,err := os.Stat(fullfn) ; err==nil {
            return fullfn, nil
          }
        }
      }

      fullfn = usrDir + "/" + fn
      if inDirectory(usrDir, fn) {
        if _,err := os.Stat(fullfn) ; err==nil {
          return fullfn, nil
        }
      }

    }

  }

  if (userid!="") {
    usrDir := USR_BASE_LOCATION + "/" + userid
    if inDirectory(usrDir, USR_BASE_LOCATION) {
      fullfn = usrDir + "/" + fn
      if inDirectory(fullfn, usrDir) {
        if _,err := os.Stat(fullfn) ; err==nil {
          return fullfn, nil
        }
      }
    }

  }

  fullfn = DEFAULT_DATA_LOCATION + "/" + fn
  if _,err := os.Stat(fullfn) ; err!=nil {
    return "", fmt.Errorf("invalid file: %s", fullfn)
  }

  return fullfn, nil
}

func FileCascadeJSON(userid, projectid, fn string) string {
  fullfn := ""

  if (userid!="") && (projectid!="") {
    usrDir := USR_BASE_LOCATION + "/" + userid
    projDir := usrDir + "/" + projectid
    if inDirectory(usrDir, USR_BASE_LOCATION) {

      if inDirectory(projDir, usrDir) {
        fullfn = projDir + "/" + fn
        if inDirectory(fullfn, projDir) {
          if _,err := os.Stat(fullfn) ; err!=nil {
            return SlurpFileJson(fullfn)
          }
        }
      }

      fullfn = usrDir + "/" + fn
      if inDirectory(usrDir, fn) {
        if _,err := os.Stat(fullfn) ; err!=nil {
          return SlurpFileJson(fullfn)
        }
      }

    }

  }

  if (userid!="") {
    usrDir := USR_BASE_LOCATION + "/" + userid
    if inDirectory(usrDir, USR_BASE_LOCATION) {
      fullfn = usrDir + "/" + fn
      if inDirectory(fullfn, usrDir) {
        if _,err := os.Stat(fullfn) ; err!=nil {
          return SlurpFileJson(fullfn)
        }
      }
    }

  }

  fullfn = DEFAULT_DATA_LOCATION + "/" + fn
  if _,err := os.Stat(fullfn) ; err!=nil {
    return `{"type":"error", "reason":"error"}`
  }

  return SlurpFileJson(fullfn)
}

func SlurpFileJson(fn string) string {
  x,e := ioutil.ReadFile(fn)
  if e!=nil {
    return `{"type":"error","reason":"error"}`
  }
  return string(x)
}

func inDirectory(fn, dir string) bool {
  f := filepath.Clean(fn)
  d := filepath.Clean(dir)
  return strings.HasPrefix(f, d)
}
