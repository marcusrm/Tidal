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
from tree import TaskTree
from pdb import set_trace as brk

# Render Task Data 
class RequesterHandlerTask(ta.BaseHandler):
	@tornado.web.authenticated
	def get(self):
		self.render("RequesterTask.html",url_prefix=ts.URL_PREFIX)

	def post(self):
		msg=self.get_argument(name="TaskInfo",default=None)
		Budget=self.get_argument(name="Budget")
		if Budget.isdigit():
			Budget=float(Budget)
		else:
			self.write('Enter Valid Inputs')
		
		# Check to see if new task was created
		if self.get_argument(name="NewTask",default=None):
			if(TaskTree.set_requestTask(msg,Budget)!=False):
				self.write('Request Submitted. Press back and logout')
			else:
				self.write('Request Being Processed. Come Back Later For Results.')
		
		# Check if Logout Button Was Pressed
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