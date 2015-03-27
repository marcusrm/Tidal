#!/usr/bin/python2.7
from tornado.ioloop import IOLoop
from tornado.web import RequestHandler, Application, url
from tornado.websocket import WebSocketHandler
from sockjs.tornado import SockJSRouter, SockJSConnection
import os
import sqlite3
import tidal_auth

settings = {
    "login_url": "/login",
    "template_path" : os.path.join(os.path.dirname(__file__), "templates"),
    "static_path"   : os.path.join(os.path.dirname(__file__), "static"),
    "debug" : True,
    "cookie_secret" : "Blorp",
    "xsrf_cookies" : False,
}
PORT=8008

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
    
    
    return Application([url(r"/login", tidal_auth.LoginHandler),
                        url(r"/logout", tidal_auth.LogoutHandler),
                        url(r"/secret", tidal_auth.secretHandler),
                        url(r"/", tidal_auth.indexHandler),
                        url(r"/.*", tidal_auth.missingHandler)]
                       ,
                       **settings
                       )

if __name__ ==  "__main__":
    app = init_app()
    app.listen(PORT)
    IOLoop.instance().start()



    
