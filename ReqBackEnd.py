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
import tree

# Render Task Data 
class RequesterHandlerTask(ta.BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render("RequesterTask.html",url_prefix=ts.URL_PREFIX)

	def post(self):
		msg=self.get_argument(name="TaskInfo",default=None)
		budget=self.get_argument(name="Budget")
		if Budget.isdigit():
			Budget=float(Budget)
		
		# Check to see if new task was created
		if self.get_argument(name="NewTask",default=None):
			if(tree.set_requestTask(msg,Budget):
				self.write('Request Submitted. Press back and logout')
			else:
				self.write('Reuqest Denied. Request already active. Only one request currently allowed.')
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