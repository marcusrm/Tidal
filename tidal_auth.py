#!/usr/bin/python2.7
from tornado.ioloop import IOLoop
from tornado.web import RequestHandler, Application, url
from tornado.websocket import WebSocketHandler
import tornado.gen
import tornado.escape
import os
import sqlite3
import hashlib, uuid
import tidal_settings as ts
import tidal_amt as t_amt
import WorkMgr as wm

def validate_username_password(target_username,target_password,mode):
    print "in validate username"
    errors = []
    bad_chars_username = set('''<>/\;:'"|{}[]-+=().,?!@#$%^&* ''')
    bad_chars_password = set('''<>/\;:'"|{}[]-+=().,''')
        
    #test some conditions & accumulate errors
    if any ((c in bad_chars_username) for c in target_username):
        errors.append("bad chars in username!")
    if any ((c in bad_chars_password) for c in target_password):
        errors.append("bad chars in password!")
    if len(target_username) > ts.MAX_SIZE_USERNAME:
        errors.append("too many characters in username!")
    if len(target_username) < ts.MIN_SIZE_USERNAME:
        errors.append("too few characters in username!")
    if len(target_password) > ts.MAX_SIZE_PASSWORD:
        errors.append("too many characters in password!")
    if len(target_password) < ts.MIN_SIZE_PASSWORD:
        errors.append("too few characters in password!")

    if errors:
        return errors
        
    conn = sqlite3.connect(ts.PASSWORD_DB)
    c = conn.cursor()
    c.execute('SELECT * FROM passwords where username = ?',
              [target_username])
    query_result = c.fetchone()
    conn.close()
    
    if query_result is not None and mode is "signup":
        errors.append("username already exists")
    elif query_result is None and mode != "signup":
        errors.append("username doesn't exist")
    elif(mode is "signin_dev" and query_result is not None 
         and query_result[2] is 0):
        errors.append("username is not a devloper")

    return errors
    
def register_new_user(username,password,is_admin):
    print "in register new user"
    
    conn = sqlite3.connect(ts.PASSWORD_DB)
    c = conn.cursor()
    with open(ts.SALT,'r') as f:
        salt = f.read()

    hashed_password = hashlib.sha512(password + salt).hexdigest()

    c.execute('INSERT INTO passwords (username,hashed_password,is_admin)'\
              'values (?,?,?)',[username,hashed_password,is_admin])
    conn.commit()
    conn.close()


def validate_worker(workerId):
    return True
    
def login_user(username, password):
    conn = sqlite3.connect(ts.PASSWORD_DB)
    c = conn.cursor()
    
    with open(ts.SALT,'r') as f:
        salt = f.read()
    hashed_password = hashlib.sha512(password + salt).hexdigest()
    
    c.execute('SELECT * FROM passwords where username = ?',[username])
    query_result = c.fetchone()
    conn.close()
    
    if query_result[1] != hashed_password:
        return ["wrong password"]
    else:
        return []
    
class BaseHandler(RequestHandler):
    def get_current_user(self):
        wrk_cookie = self.get_secure_cookie("wrk")
        req_cookie = self.get_secure_cookie("req")
        dev_cookie = self.get_secure_cookie("dev")
        
        if(dev_cookie is not None):
            print "dev cookie"
            return dev_cookie
        
        if((ts.URL_PREFIX+"/dev") not in self.request.uri and
           (ts.URL_PREFIX+"/hit") not in self.request.uri and
           req_cookie is not None):
            print "req cookie"
            return req_cookie

        if(wrk_cookie is not None and
           ts.URL_PREFIX+"/hit" in self.request.uri ):
           #and self.request.remote_ip is "192.168.1.1") : #todo, AMT ip
            print "worker cookie"
            return wrk_cookie

        print "no cookie"
        
class reqLoginHandler(BaseHandler):
    def get(self):
        if not self.current_user:
            self.write("get a cookie.")
        else:
            self.write("you have a cookie.<br>")
            self.write("your cookie is: "+self.current_user)
            
        self.render("rlogin.html",url_prefix=ts.URL_PREFIX)
        
    def post(self):
        if self.current_user: #if they're already logged in:
            self.redirect(ts.URL_PREFIX+"/secret")
        else:
            username = self.get_argument("username")
            password = self.get_argument("password")
            errs= []
            
            if self.get_argument("submit_button") == "Sign up":
                errs += validate_username_password(username,password,"signup")
                if not errs:     #username and password were fomatted well                  
                    register_new_user(username,password,0)
                    self.set_secure_cookie("req",
                                           self.get_argument("username"), 
                                           expires_days=None)
                    
            elif( self.get_argument("submit_button") == "Sign in"):
                errs += validate_username_password(username,password,"signin")
                if not errs:
                    print errs
                    errs += login_user(username,password)
                if not errs:
                    self.set_secure_cookie("req",
                                           self.get_argument("username"),
                                           expires_days=None)
                    
            else:
                self.write("No cheating!"); return

            if errs :
                for x in (errs):
                    self.write(x+"<br>")
                self.render("rlogin.html",url_prefix=ts.URL_PREFIX)
            else:
                self.redirect(ts.URL_PREFIX+"/secret")    
          
class devLoginHandler(BaseHandler):
    def get(self):
        if not self.current_user:
            self.write("get a cookie.")
        else:
            self.write("you have a cookie.<br>")
            self.write("your cookie is: "+self.current_user)
            
        self.render("dlogin.html",url_prefix=ts.URL_PREFIX)
        
    def post(self):
        if self.current_user: #if they're already logged in:
            self.redirect(ts.URL_PREFIX+"/secret")
        else:
            username = self.get_argument("username")
            password = self.get_argument("password")
            errs = validate_username_password(username,password,"signin_dev")
            if not errs:                    
                errs += login_user(username,password)
            if not errs:
                self.set_secure_cookie("dev",
                                       self.get_argument("username"),
                                       expires_days=None)
                
            
            if errs :
                for x in (errs):
                    self.write(x+"<br>")
                self.render("dlogin.html",url_prefix=ts.URL_PREFIX)
            else:
                self.redirect(ts.URL_PREFIX+"/secret")    
                
class wrkLoginHandler(BaseHandler):
    def get(self):
        workerId = self.get_argument("workerId",None)
        assignmentId = self.get_argument("assignmentId",None)
        hitId = self.get_argument("hitId",None)

        # if(self.request.remote_ip is not AMT_IP):
        #     self.write("not an official request from AMT")
        #     self.render("404.html")
        print assignmentId
        if( assignmentId is None or
                assignmentId == "ASSIGNMENT_ID_NOT_AVAILABLE"):
                self.render("hit_preview.html")
        
        elif(hitId is None or workerId is None ):
            self.write("Missing worker or hit ID")
            self.render("404.html")
            
        elif(not t_amt.hit_exists(hitId)):
            self.write("bad task id or worker ID")
            self.render("404.html")
            
        else:
            if(not wm.W.WIDexist(workerId)):
                wm.W.add(workerId)
            wm.W.login(workerId,assignmentId)
            
            self.set_secure_cookie("wrk",workerId,expires_days=None)
            
            self.redirect(ts.URL_PREFIX+"/hit"+"?workerId="+workerId+"&hitId="+hitId)
            #you can add more or less arguments here. You probably don't
            #need anything besides the worker id and the amt_task_id,
            #which you can use to look up info on that amt HIT. I think it's
            #probably just as good as having the assignment id.
            
            
class loginHandler(BaseHandler):
    def get(self):
        self.render("login.html",url_prefix=ts.URL_PREFIX)
    def post(self):
        if self.get_argument("requester",None):
            self.redirect(ts.URL_PREFIX+"/rlogin")
        if self.get_argument("developer",None):
            self.redirect(ts.URL_PREFIX+"/dlogin")
        
class logoutHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.clear_all_cookies()
        self.render("logout.html")

class secretHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render("secret.html",url_prefix=ts.URL_PREFIX)

    def post(self):
        if self.get_argument("logout",None):
            self.redirect(ts.URL_PREFIX+"/logout")
        if self.get_argument("login",None):
            self.redirect(ts.URL_PREFIX+"/login")

class missingHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render("404.html",url_prefix=ts.URL_PREFIX)        

def init_password_db():    
    password_db_missing = not os.path.exists(ts.PASSWORD_DB)
    if(password_db_missing):
        conn = sqlite3.connect(ts.PASSWORD_DB)
        c = conn.cursor()
        with open(ts.PASSWORD_SCHEMA,'rt') as f:
            schema = f.read()
        c.executescript(schema)
        conn.close()
        
    salt_missing = not os.path.exists(ts.SALT)
    if(salt_missing):
        salt = uuid.uuid4().hex
        with open(ts.SALT,'w') as f:
            f.write(salt)

    #if we had to reinit the password db, add the admin.
    if(password_db_missing):
        register_new_user("adminadmin","crowdcrowd",1)



            
