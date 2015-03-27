#!/usr/bin/python2.7
from tornado.ioloop import IOLoop
from tornado.web import RequestHandler, Application, url
from tornado.websocket import WebSocketHandler
from sockjs.tornado import SockJSRouter, SockJSConnection
import tornado.gen
import tornado.escape
import os
import sqlite3
import hashlib, uuid

settings = {
    "login_url": "/login",
    "template_path" : os.path.join(os.path.dirname(__file__), "templates"),
    "static_path"   : os.path.join(os.path.dirname(__file__), "static"),
    "debug" : True,
    "cookie_secret" : "Blorp",
    "xsrf_cookies" : False,
}
    
active_users = set()
PASSWORD_DB = 'static/passwords.db'
PASSWORD_SCHEMA = 'static/passwords.sql'
SALT = 'static/salt.bin'
MAX_SIZE_USERNAME=32
MAX_SIZE_PASSWORD=32
MIN_SIZE_USERNAME=8
MIN_SIZE_PASSWORD=8
    
def validate_username_password(target_username,target_password):
    print "in validate username"
    errors = []
    bad_chars_username = set('''<>/\;:'"|{}[]-+=().,?!@#$%^&* ''')
    bad_chars_password = set('''<>/\;:'"|{}[]-+=().,''')
    
    conn = sqlite3.connect(PASSWORD_DB)
    c = conn.cursor()
    c.execute('SELECT * FROM passwords where username = ?',
              [target_username])
    query_result = c.fetchone()
    conn.close()
    
    if query_result is not None:
        errors.append("username already exists")
        
    #test some conditions & accumulate errors
    if any ((c in bad_chars_username) for c in target_username):
        errors.append("bad chars in username!")
    if any ((c in bad_chars_password) for c in target_password):
        errors.append("bad chars in password!")
    if len(target_username) > MAX_SIZE_USERNAME:
        errors.append("too many characters in username!")
    if len(target_username) < MIN_SIZE_USERNAME:
        errors.append("too few characters in username!")
    if len(target_password) > MAX_SIZE_PASSWORD:
        errors.append("too many characters in password!")
    if len(target_password) < MIN_SIZE_PASSWORD:
        errors.append("too few characters in password!")
        
    return errors
    
def register_new_user(username,password):
    print "in register new user"
    
    conn = sqlite3.connect(PASSWORD_DB)
    c = conn.cursor()
    with open(SALT,'r') as f:
        salt = f.read()

    hashed_password = hashlib.sha512(password + salt).hexdigest()

    c.execute('INSERT INTO passwords (username,hashed_password)'\
              'values (?,?)',[username,hashed_password])
    conn.commit()
    conn.close()

def login_user(username, password):
    print "hi"
    
class BaseHandler(tornado.web.RequestHandler):
    #overload get_current_user function
    #to return username only if it's attached to
    #a cookie.
    def get_current_user(self):
        return self.get_secure_cookie("user")
        
class LoginHandler(BaseHandler):
    def get(self):
        if not self.current_user:
            self.write("get a cookie.")
        else:
            self.write("you have a cookie.<br>")
            self.write("your cookie is: "+self.current_user)
            
        self.render("login.html")
        
    def post(self):
        if self.current_user: #if they're already logged in:
            self.redirect("/secret")
        else:
            username = self.get_argument("username");
            password = self.get_argument("password");
            errs = validate_username_password(username,password);
            if not errs:        
                register_new_user(username,password)
                self.set_secure_cookie("user", self.get_argument("username"))
                self.redirect("/secret")
            else:
                for x in (errs):
                    self.write(x+"<br>");
                self.render("login.html")
            
        
class LogoutHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.clear_cookie("user")
        self.render("logout.html")

class secretHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render("secret.html")

    def post(self):
        if self.get_argument("logout"):
            self.redirect("/logout")

class indexHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render("index.html")
        
def init_app():
    #loginRouter = SockJSRouter(loginConnection,'/login')

    password_db_missing = not os.path.exists(PASSWORD_DB)
    if(password_db_missing):
        conn = sqlite3.connect(PASSWORD_DB)
        c = conn.cursor()
        with open(PASSWORD_SCHEMA,'rt') as f:
            schema = f.read()
        c.executescript(schema)
        conn.close()
        
    salt_missing = not os.path.exists(SALT)
    if(salt_missing):
        salt = uuid.uuid4().hex
        with open(SALT,'w') as f:
            f.write(salt)
    
    
    return Application([url(r"/login", LoginHandler),
                        url(r"/logout", LogoutHandler),
                        url(r"/secret", secretHandler),
                        url(r"/", indexHandler)]
                       #+ loginRouter.urls,
                       ,
                       **settings
                       )

if __name__ ==  "__main__":
    app = init_app()
    app.listen(8008)
    IOLoop.instance().start()



    
