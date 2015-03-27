#!/usr/bin/python2.7
from tornado.ioloop import IOLoop
from tornado.web import RequestHandler, Application, url
from tornado.websocket import WebSocketHandler
from sockjs.tornado import SockJSRouter, SockJSConnection
import tornado.gen
import os
import sqlite3

active_users = set()

settings = {
    "login_url": "/login",
    "template_path" : os.path.join(os.path.dirname(__file__), "templates"),
    "static_path"   : os.path.join(os.path.dirname(__file__), "static"),
    "debug" : True,
    "cookie_secret" : "Blorp",
    "xsrf_cookies" : False,
}
    
# class EchoConnection(SockJSConnection):

#     def on_open(self, info):
#         # Send that someone joined
#         #print "JOINED!!"
#         self.broadcast(self.active_users, "New Player!")

#         # Add client to the clients list
#         self.active_users.add(self)

#     def on_message(self, message):
#         # Broadcast message
#         #print "bc!!"
#         self.broadcast(self.active_users, message)

#     def on_close(self):
#         # Remove client from the clients list and broadcast leave message
#         #print "CLOSED"
#         self.active_users.remove(self)

#         self.broadcast(self.active_users, "X disconnected...")

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
        if self.current_user:
            self.redirect("/login")
        else:
            self.set_secure_cookie("user", self.get_argument("username"))
            self.redirect("/secret")
            
        
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
        
def make_app():
    EchoRouter = SockJSRouter(EchoConnection,'/echo')
    return Application([url(r"/login", LoginHandler),
                        url(r"/logout", LogoutHandler),
                        url(r"/secret", secretHandler),
                        url(r"/", indexHandler)]
                       + EchoRouter.urls,
                       **settings
                       )

if __name__ ==  "__main__":
    app = make_app()
    app.listen(8008)
    IOLoop.instance().start()



    
