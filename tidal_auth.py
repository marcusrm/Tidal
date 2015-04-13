
from tornado.ioloop import IOLoop
from tornado.web import RequestHandler, Application, url
from tornado.websocket import WebSocketHandler
from sockjs.tornado import SockJSRouter, SockJSConnection
import tornado.gen
import tornado.escape
import os
import sqlite3
import hashlib, uuid
import tidal_settings as ts
import tidal_amt as t_amt

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

    if errors is not None:
        return errors
        
    conn = sqlite3.connect(ts.PASSWORD_DB)
    c = conn.cursor()
    c.execute('SELECT * FROM passwords where username = ?',
              [target_username])
    query_result = c.fetchone()
    conn.close()
    
    if query_result is not None and mode is "signup":
        errors.append("username already exists")
    elif query_result is None and mode is not "signup":
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
            return req_cookie

        if(wrk_cookie is not None and
           self.request.uri is ts.URL_PREFIX+"/hit" and
           self.request.remote_ip is "192.168.1.1"): #todo, AMT ip
            print "worker cookie"
            return wrk_cookie

        
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
        workerId = self.get_argument("workerId")
        task_id = self.get_argument("task_id")
        assignmentId = self.get_argument("assignmentId")

        # if(self.request.remote_ip is not AMT_IP):
        #     self.write("not an official request from AMT")
        #     self.render("404.html")

        elif(task_id is None or workerId is None ):
            self.write("Missing worker or task ID")
            self.render("404.html")

        elif(task_id not in amt_task_ids or not validate_worker(workerId)):
            self.write("bad task id or worker ID")
            self.render("404.html")
            
        else:
            if( assignmentId is None or
                assignmentId is "ASSIGNMENT_ID_NOT_AVAILABLE"):
                self.render("hit_preview.html")
            else:
                amt_task_ids.remove(task_id) #remove this task_id
                ts.t_pending.add(task_id) #move task to pending
                w.add(workerId)#add worker to pool

                #post new hits if hits < min. add to list 
                if(len(ts.task_amt) < ts.task_amt_desired):
                    new_hits = t_amt.post_hit(ts.T_AMT_MIN - len(ts.task_amt))
                    ts.task_amt
                self.redirect(ts.URL_PREFIX+"/hit")
                
        else:
            self.write("fallthrough on wrklogin.")
            self.render("404.html")
            
            
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

# class hitHandler(BaseHandler):
#     @tornado.web.authenticated
#     def get(self): 
#         self.render("hit.html",url_prefix=ts.URL_PREFIX)
        
class missingHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render("404.html",url_prefix=ts.URL_PREFIX)
        




            
