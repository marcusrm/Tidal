#!/usr/bin/python2.7
from tornado.ioloop import IOLoop
from tornado.web import RequestHandler, Application, url
from tornado.websocket import WebSocketHandler
import os
import sqlite3
import hashlib, uuid
import tidal_auth as ta
import tidal_settings as ts
import tidal_amt as t_amt
import sys
sys.path.append("./TaskMgr")
import TaskMgr as tm
import ReqBackEnd as rbe
import WorkMgr as wm

# Initialize the WrkDatabase
wm.W.WMinit()

app_settings = {
    "login_url": ts.URL_PREFIX+"/login",
    "template_path" : os.path.join(os.path.dirname(__file__), "templates"),
    "static_path"   : os.path.join(os.path.dirname(__file__), "static"),
    "debug" : True,
    "cookie_secret" : "Blorp",
    "xsrf_cookies" : False,
}

def init_app():

    ta.init_password_db()

    if(not ts.LOCAL_TESTING):
        t_amt.init_amt_hit_db()
        t_amt.cancel_hits()
        t_amt.post_hit(3)
            
    return Application([url(ts.URL_PREFIX+ r"/rlogin", ta.reqLoginHandler),
                        url(ts.URL_PREFIX+ r"/dlogin", ta.devLoginHandler),
                        url(ts.URL_PREFIX+ r"/wlogin", ta.wrkLoginHandler),
                        url(ts.URL_PREFIX+ r"/login", ta.loginHandler),
                        url(ts.URL_PREFIX+ r"/logout", ta.logoutHandler),
                        url(ts.URL_PREFIX+ r"/RequesterTaskMgr", rbe.RequesterHandlerTask),
						url(ts.URL_PREFIX+ r"/RequesterWorkMgr", rbe.RequesterHandlerWork),
                        url(ts.URL_PREFIX+ r"/hit", tm.hitHandler),
                        url(ts.URL_PREFIX+ r"/websocket", tm.WebSocketHandler),
                        url(r"/.*", ta.missingHandler)]
                       ,
                       **app_settings
                       )

if __name__ ==  "__main__":
    app = init_app()
    print ts.PORT
    app.listen(ts.PORT)
    IOLoop.instance().start()



    
