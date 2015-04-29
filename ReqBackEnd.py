from tornado.ioloop import IOLoop
from tornado.web import RequestHandler, Application, url
#from tornado.websocket import WebSocketHandler
import tornado.gen
import tornado.escape
import tidal_auth as ta
import sys; sys.path.append("./TaskMgr");
import TaskMgr as tm
import WorkMgr as wm
import tidal_settings as ts

# Render Task Data 
class RequesterHandlerTask(ta.BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render("RequesterTask.html",url_prefix=ts.URL_PREFIX)

	def post(self):
		if self.get_argument(name="NewTask",default=None):
			self.redirect(ts.URL_PREFIX+"/logout")
        if self.get_argument("logout",None):
			self.redirect(ts.URL_PREFIX+"/logout")
        if self.get_argument("login",None):
			self.redirect(ts.URL_PREFIX+"/login")
			
# Render Worker Data 
class RequesterHandlerWork(ta.BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render("RequesterWork.html",url_prefix=ts.URL_PREFIX)

    def post(self):
        if self.get_argument("logout",None):
            self.redirect(ts.URL_PREFIX+"/logout")
        if self.get_argument("login",None):
            self.redirect(ts.URL_PREFIX+"/login")