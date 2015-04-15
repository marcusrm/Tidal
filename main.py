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

app_settings = {
    "login_url": ts.URL_PREFIX+"/login",
    "template_path" : os.path.join(os.path.dirname(__file__), "templates"),
    "static_path"   : os.path.join(os.path.dirname(__file__), "static"),
    "debug" : True,
    "cookie_secret" : "Blorp",
    "xsrf_cookies" : False,
}

def init_app():
    
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
        ta.register_new_user("adminadmin","crowdcrowd",1)

    #should check AMT for already posted hits, but for now
    #let's just make some new ones upon startup.
    t_amt.cancel_hits()
    if(len(ts.task_amt) < ts.task_amt_desired):
        new_hits = t_amt.post_hit(ts.task_amt_desired - len(ts.task_amt))
        ts.task_amt.update(new_hits)
            
    return Application([url(ts.URL_PREFIX+ r"/rlogin", ta.reqLoginHandler),
                        url(ts.URL_PREFIX+ r"/dlogin", ta.devLoginHandler),
                        url(ts.URL_PREFIX+ r"/wlogin", ta.wrkLoginHandler),
                        url(ts.URL_PREFIX+ r"/login", ta.loginHandler),
                        url(ts.URL_PREFIX+ r"/logout", ta.logoutHandler),
                        url(ts.URL_PREFIX+ r"/secret", ta.secretHandler),
                        url(ts.URL_PREFIX+ r"/hit", tm.hitHandler),
                        url(r"/.*", ta.missingHandler),
                        url(ts.URL_PREFIX+ r"/websocket", tm.WebSocketHandler)]
                       ,
                       **app_settings
                       )

if __name__ ==  "__main__":
    app = init_app()
    app.listen(ts.PORT)
    IOLoop.instance().start()



    
