from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from inspect import getargspec
import urlparse

import json

from src.LlamaDB import get_llama

class BaseHTTPcustomServer(BaseHTTPRequestHandler):
    stored_post_data = {}
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

    def do_HEAD(self):
        self._set_headers() 
    def do_OPTIONS(self):           
        self.send_response(200, "ok")       
        self.send_header('Access-Control-Allow-Origin', '*')                
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header("Access-Control-Allow-Headers", "X-Requested-With")     
        self.send_header("Access-Control-Allow-Headers", "Content-Type")   
    def extract_json(self,val) :
		if type(val) is list : return val[0]
		if type(val) in [unicode,int] : return val
		return None

    def log(self,msg):
		BaseHTTPRequestHandler.log_message(self,msg)

    def authQuery(self) :
		try : 
			p = urlparse.urlparse(self.path)
			q =  urlparse.parse_qs(p.query)
			u = int( self.extract_json(q["uid"]) )
			return u
		except KeyError:
			pass
		return False	
    def getStoredPostData(self):
		return self.stored_post_data
    def getPostData(self):
		content_length=int(self.headers['Content-Length']) 
		content_type=(self.headers['Content-Type']) 
		post_data = self.rfile.read(content_length) 
		content_type = content_type.split(";")
		if "application/json" in content_type :
			self.stored_post_data = json.loads(post_data)
		else :
			self.stored_post_data =  urlparse.parse_qs(post_data)
		return self.stored_post_data
    def authPostData(self):
		try:
			post_data = self.getPostData()
			uid =  self.extract_json(post_data["uid"])
			if (uid != None ):
				return int(uid)
		except KeyError:
			pass
		return False	
    def executeCustomFun(self,fun,llama,u) :
		data = {}
		sig = getargspec(fun)
		ps = sig.args
		parameters = []
		for p in ps :
			if p != "self" : 
				parameters.append(p)
		try :
			if llama == None or (len(parameters) == 0 ) :
				data = fun()
			elif (len(parameters) == 1 ) :
				data = fun(llama)
			elif (len(sig.parameters) == 2 ) :
				data = fun(llama,u)
			return data
		except TypeError:
			return { "type" : "error", "data" : "suca" }
    def executeCustomFunWithData(self,fun,llama,u,post_data) :
		data = {}
		sig = getargspec(fun)
		ps = sig.args
		parameters = []
		for p in ps :
			if p != "self" : 
				parameters.append(p)
		if llama == None or (len(parameters) == 1 ) :
			data = fun(post_data)
		elif (len(parameters) == 2 ) :
			data = fun(llama,post_data)
		elif (len(sig.parameters) == 3 ) :
			data = fun(llama,u,post_data)
		return data
    def customGET(self,fun) :
		try :
			self._set_headers()
			u = self.authQuery()
			llama = get_llama(u)
		except KeyError :
			u = - 1
			llama = None
		data = self.executeCustomFun(fun,llama,u)
		msg = json.dumps(data)
		self.wfile.write(msg)
		
    def customPOST(self,fun) :
		try :
			self._set_headers() 
			u = self.authPostData()
			llama = get_llama(u)
		except KeyError :
			u = - 1
			llama = None
		data = self.executeCustomFunWithData(fun,llama,u,self.getStoredPostData())
		msg = json.dumps(data)
		self.wfile.write(msg)
		

			