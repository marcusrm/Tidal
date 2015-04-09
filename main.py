#!/usr/bin/python2.7
from tornado.ioloop import IOLoop
from tornado.web import RequestHandler, Application, url
from tornado.websocket import WebSocketHandler
from sockjs.tornado import SockJSRouter, SockJSConnection
import os
import sqlite3
import tidal_auth
import hashlib, uuid


PORT=8008
URL_PREFIX = '/%02d'%(PORT % 100)

settings = {
    "login_url": URL_PREFIX+"/login",
    "template_path" : os.path.join(os.path.dirname(__file__), "templates"),
    "static_path"   : os.path.join(os.path.dirname(__file__), "static"),
    "debug" : True,
    "cookie_secret" : "Blorp",
    "xsrf_cookies" : False,
}

def init_app():
    
    password_db_missing = not os.path.exists(tidal_auth.PASSWORD_DB)
    if(password_db_missing):
        conn = sqlite3.connect(tidal_auth.PASSWORD_DB)
        c = conn.cursor()
        with open(tidal_auth.PASSWORD_SCHEMA,'rt') as f:
            schema = f.read()
        c.executescript(schema)
        conn.close()
        
    salt_missing = not os.path.exists(tidal_auth.SALT)
    if(salt_missing):
        salt = uuid.uuid4().hex
        with open(tidal_auth.SALT,'w') as f:
            f.write(salt)

    #if we had to reinit the password db, add the admin.
    if(password_db_missing):
        tidal_auth.register_new_user("adminadmin","crowdcrowd",1)
            
    return Application([url(URL_PREFIX+ r"/rlogin", tidal_auth.reqLoginHandler),
                        url(URL_PREFIX+ r"/dlogin", tidal_auth.devLoginHandler),
                        url(URL_PREFIX+ r"/wlogin", tidal_auth.wrkLoginHandler),
                        url(URL_PREFIX+ r"/login", tidal_auth.loginHandler),
                        url(URL_PREFIX+ r"/logout", tidal_auth.logoutHandler),
                        url(URL_PREFIX+ r"/secret", tidal_auth.secretHandler),
                        url(URL_PREFIX+ r"/hit", tidal_auth.hitHandler),
                        url(URL_PREFIX+ r"/", tidal_auth.indexHandler),
                        url(r"/.*", tidal_auth.missingHandler)]
                       ,
                       **settings
                       )

if __name__ ==  "__main__":
    app = init_app()
    app.listen(PORT)
    IOLoop.instance().start()



    
