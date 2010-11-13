import SimpleHTTPServer
import SocketServer
import time
from datetime import datetime, timedelta
import sqlite3

PORT = 80

svr_doc_time = time.time()
msg_cache = list()

class Message():
    def __init__(self, msgbody, timestamp):
        self.timestamp = timestamp
        self.msgbody = msgbody

class MyHTTPServer(SimpleHTTPServer.SimpleHTTPRequestHandler):
    def do_GET(self):
        global svr_doc_time, msg_cache
        print 'path ', self.path
        if self.path == '/checkpoint1':
            svr_doc_time = '%8.2f' % time.clock()
            self.send_response(200)
            self.send_header(u'Content-type', u'text/html')
            self.end_headers()
            self.wfile.write(svr_doc_time)
        elif self.path.startswith('/send_text/'):
            # recieve message from client
            svr_doc_time = time.time()
            text = self.path
            text = text.replace('/send_text/', '')
            msg = Message(text, svr_doc_time)
            msg_cache.append(msg)
            self.send_response(200)
            self.send_header(u'Content-type', u'text/html')
            self.end_headers()
            self.wfile.write(svr_doc_time)
        elif self.path.startswith('/timestamp/'):
            # check if upate is required
            client_doc_time = self.path
            client_doc_time = client_doc_time.replace('/timestamp/', '')
            client_doc_time = client_doc_time.replace('%20', ' ')
            print 'TIMESTAMP ', client_doc_time
            update = 'false';
            if float(svr_doc_time) > float(client_doc_time):
                update = 'true';
            ret = """server time: %s<br/>
            client time: %s<br/>
            require update: %s
            """ % (svr_doc_time, client_doc_time, update)
            print ret
            self.send_response(200)
            self.send_header(u'Content-type', u'text/html')
            self.end_headers()
            self.wfile.write(ret)
        elif self.path == '/':
            with open('template.html') as hfile:
                template = hfile.read()
            template = template % str(svr_doc_time)
            self.send_response(200)
            self.send_header(u'Content-type', u'text/html')
            self.end_headers()
            self.wfile.write(template)
        return
    def do_POST(self):
        print 'path ', self.path

Handler = MyHTTPServer

httpd = SocketServer.TCPServer(("", PORT), Handler)

print "serving at port", PORT
httpd.serve_forever()