﻿"""Simple HTTP server based on the asyncore / asynchat framework

Under asyncore, every time a socket is created it enters a table which is
scanned through select calls by the asyncore.loop() function

All events (a client connecting to a server socket, a client sending data,
a server receiving data) is handled by the instances of classes derived
from asyncore.dispatcher

Here the server is represented by an instance of the Server class

When a client connects to it, its handle_accept() method creates an
instance of RequestHandler, one for each HTTP request. It is derived
from asynchat.async_chat, a class where incoming data on the connection
is processed when a "terminator" is received. The terminator can be :
- a string : here we'll use the string \r\n\r\n to handle the HTTP request
line and the HTTP headers
- an integer (n) : the data is processed when n bytes have been read. This
will be used for HTTP POST requests

The data is processed by a method called found_terminator. In RequestHandler,
found_terminator is first set to handle_request_line to handle the HTTP
request line (including the decoding of the query string) and the headers.
If the method is POST, terminator is set to the number of bytes to read
(the content-length header), and found_terminator is set to handle_post_data

After that, the handle_data() method is called and the connection is closed

Subclasses of RequestHandler only have to override the handle_data() method
"""

import asynchat, asyncore, socket, SimpleHTTPServer, select, urllib
import posixpath, sys, cgi, cStringIO, os, traceback, shutil

class CI_dict(dict):
    """Dictionary with case-insensitive keys
    Replacement for the deprecated mimetools.Message class
    """

    def __init__(self, infile, *args):
        self._ci_dict = {}
        lines = infile.readlines()
        for line in lines:
            k,v=line.split(":",1)
            self._ci_dict[k.lower()] = self[k] = v.strip()
        self.headers = self.keys()

    def getheader(self,key,default=""):
        return self._ci_dict.get(key.lower(),default)

    def get(self,key,default=""):
        return self._ci_dict.get(key.lower(),default)

    def __getitem__(self,key):
        return self._ci_dict[key.lower()]

    def __contains__(self,key):
        return key.lower() in self._ci_dict

class socketStream:

    def __init__(self,sock):
        """Initiate a socket (non-blocking) and a buffer"""
        self.sock = sock
        self.buffer = cStringIO.StringIO()
        self.closed = 1   # compatibility with SocketServer

    def write(self, data):
        """Buffer the input, then send as many bytes as possible"""
        self.buffer.write(data)
        if self.writable():
            buff = self.buffer.getvalue()
            # next try/except clause suggested by Robert Brown
            try:
                    sent = self.sock.send(buff)
            except:
                    # Catch socket exceptions and abort
                    # writing the buffer
                    sent = len(data)

            # reset the buffer to the data that has not yet be sent
            self.buffer=cStringIO.StringIO()
            self.buffer.write(buff[sent:])

    def finish(self):
        """When all data has been received, send what remains
        in the buffer"""
        data = self.buffer.getvalue()
        # send data
        while len(data):
            while not self.writable():
                pass
            sent = self.sock.send(data)
            data = data[sent:]

    def writable(self):
        """Used as a flag to know if something can be sent to the socket"""
        return select.select([],[self.sock],[])[1]

class RequestHandler(asynchat.async_chat,
    SimpleHTTPServer.SimpleHTTPRequestHandler):

    protocol_version = "HTTP/1.1"
    MessageClass = CI_dict

    def __init__(self,conn,addr,server):
        asynchat.async_chat.__init__(self,conn)
        self.client_address = addr
        self.connection = conn
        self.server = server
        # set the terminator : when it is received, this means that the
        # http request is complete ; control will be passed to
        # self.found_terminator
        self.set_terminator ('\r\n\r\n')
        self.rfile = cStringIO.StringIO()
        self.found_terminator = self.handle_request_line
        self.request_version = "HTTP/1.1"
        # buffer the response and headers to avoid several calls to select()
        self.wfile = cStringIO.StringIO()

    def collect_incoming_data(self,data):
        """Collect the data arriving on the connexion"""
        self.rfile.write(data)

    def prepare_POST(self):
        """Prepare to read the request body"""
        bytesToRead = int(self.headers.getheader('content-length'))
        # set terminator to length (will read bytesToRead bytes)
        self.set_terminator(bytesToRead)
        self.rfile = cStringIO.StringIO()
        # control will be passed to a new found_terminator
        self.found_terminator = self.handle_post_data

    def handle_post_data(self):
        """Called when a POST request body has been read"""
        self.rfile.seek(0)
        self.do_POST()
        self.finish()

    def do_GET(self):
        """Begins serving a GET request"""
        # nothing more to do before handle_data()
        self.body = {}
        self.handle_data()

    def do_POST(self):
        """Begins serving a POST request. The request data must be readable
        on a file-like object called self.rfile"""
        ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
        self.body = cgi.FieldStorage(fp=self.rfile,
            headers=self.headers, environ = {'REQUEST_METHOD':'POST'},
            keep_blank_values = 1)
        self.handle_data()

    def handle_data(self):
        """Class to override"""
        f = self.send_head()
        if f:
            self.copyfile(f, self.wfile)

    def handle_request_line(self):
        """Called when the http request line and headers have been received"""
        # prepare attributes needed in parse_request()
        self.rfile.seek(0)
        self.raw_requestline = self.rfile.readline()
        self.parse_request()

        if self.command in ['GET','HEAD']:
            # if method is GET or HEAD, call do_GET or do_HEAD and finish
            method = "do_"+self.command
            if hasattr(self,method):
                getattr(self,method)()
                self.finish()
        elif self.command=="POST":
            # if method is POST, call prepare_POST, don't finish yet
            self.prepare_POST()
        else:
            self.send_error(501, "Unsupported method (%s)" %self.command)

    def end_headers(self):
        """Send the blank line ending the MIME headers, send the buffered
        response and headers on the connection, then set self.wfile to
        this connection
        This is faster than sending the response line and each header
        separately because of the calls to select() in socketStream"""
        if self.request_version != 'HTTP/0.9':
            self.wfile.write("\r\n")
        self.start_resp = cStringIO.StringIO(self.wfile.getvalue())
        self.wfile = socketStream(self.connection)
        self.copyfile(self.start_resp, self.wfile)

    def handle_error(self):
        traceback.print_exc(sys.stderr)
        self.close()

    def copyfile(self, source, outputfile):
        """Copy all data between two file objects
        Set a big buffer size"""
        shutil.copyfileobj(source, outputfile, length = 128*1024)

    def finish(self):
        """Send data, then close"""
        try:
            self.wfile.finish()
        except AttributeError:
            # if end_headers() wasn't called, wfile is a StringIO
            # this happens for error 404 in self.send_head() for instance
            self.wfile.seek(0)
            self.copyfile(self.wfile, socketStream(self.connection))
        self.close()

class Server(asyncore.dispatcher):
    """Copied from http_server in medusa"""
    def __init__ (self, ip, port, handler):
        self.ip = ip
        self.port = port
        self.handler = handler
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)

        self.set_reuse_addr()
        self.bind((ip, port))

        # lower this to 5 if your OS complains
        self.listen(1024)

    def handle_accept(self):
        try:
            conn, addr = self.accept()
        except socket.error:
            self.log_info('warning: server accept() threw an exception', 'warning')
            return
        except TypeError:
            self.log_info('warning: server accept() threw EWOULDBLOCK', 'warning')
            return
        # creates an instance of the handler class to handle the request/response
        # on the incoming connexion
        self.handler(conn, addr, self)

"""Above codes are
Recipe 440665: Asynchronous HTTP server (Python)
imported from
http://code.activestate.com/recipes/440665-asynchronous-http-server/

"""

import os
import time
import cgi
import json

class Message():
    def __init__(self, author, body):
        self.timestamp = float(str(time.time())) # so the precision matches those in client document
        self.author = author
        self.body = body

svr_doc_time = time.time()
msg_cache = []

msg = Message(u'Project: 2501', u"""Hello&#44; world!<br/>
    哈羅，沃爾德！<br/>
    """)
msg_cache.append(msg)

html_escape_table = {
    "&": "&amp;",
    '"': "&quot;",
    "'": "&#39",
    ">": "&gt;",
    "<": "&lt;",
    "=": "&#61",
    ",": "&#44;",
    }

def html_escape(text):
    """Produce entities within text."""
    return "".join(html_escape_table.get(c,c) for c in text)

def get_msg():
    return msg.encode('utf-8')

class MyHandler(RequestHandler):
    def handle_get(self):
        self.path = 'html' + self.path
        print 'try ', self.path
        if not os.path.isfile(self.path):
            self.path = '/html/template.html'
            print 'else ', self.path
        RequestHandler.handle_data(self)

    def handle_post(self):
        global svr_doc_time, msg_cache
        print 'path: ', self.path
        if self.path == '/send_text/':
            # recieve message from client
            svr_doc_time = time.time()

            # preprocess the message
            text = self.rfile.getvalue()
            text = unicode(text, 'utf-8')
            text = html_escape(text)
            text = text.replace('\n', '<br/>')

            # append message
            # author is for test only, should replace with user id
            # still, ip should be saved in message entity
            author = self.client_address[0]
            author = unicode(author, 'utf-8')
            print 'author: ', author
            msg = Message(author, text)
            msg_cache.append(msg)

            #msg = Message(text, svr_doc_time)
            #msg_cache.append(msg)
            self.send_response(204)
            self.end_headers()

        elif self.path == '/check_update/':
            client_doc_time = self.rfile.getvalue()
            #print 'client document time: ', float(client_doc_time)
            #print 'type: ', type(float(client_doc_time))

            # compose return string
            rethtml = u'';
            rettime = None;
            htmlclass = u'odd'
            for msg in msg_cache:
                #print 'json: ', json.dumps(msg)
                #print 'message time: ', msg.timestamp
                #print 'type: ', type(msg.timestamp)
                #print 'diff: ', msg.timestamp-float(client_doc_time)
                if msg.timestamp-float(client_doc_time) > 1e-3:
                    #rethtml = rethtml + u'<p class="' + htmlclass + u'">'
                    rethtml = rethtml + u'<p>'
                    rethtml = rethtml + u'<b>' + msg.author + u'</b> at ' \
                        + str(msg.timestamp) + u'<br/>'
                    rethtml = rethtml + u'<blockquote>'
                    rethtml = rethtml + msg.body
                    rethtml = rethtml + u'</blockquote>'
                    rethtml = rethtml + u'</p>'
                    rettime = str(msg.timestamp)
                if htmlclass == u'odd':
                    htmlclass = u'even'
                else:
                    htmlclass = u'odd'

            if rettime:
                ret = 'timestamp=%s,msg=%s' % (rettime, rethtml.encode('utf-8'))
                print 'msg: ', ret
                self.send_response(200)
                self.send_header(u'Content-type', u'text/html')
                self.end_headers()
                self.wfile.write(ret)
            else:
                self.send_response(204)
                self.end_headers()

    def handle_data(self):
        if self.command == 'GET':
            self.handle_get()
        elif self.command == 'POST':
            self.handle_post()

if __name__=="__main__":
    # launch the server on the specified port
    port = 8081
    s = Server('', port, MyHandler)
    print "SimpleAsyncHTTPServer running on port %s" % port
    try:
        asyncore.loop(timeout=2)
    except KeyboardInterrupt:
        print "Crtl+C pressed. Shutting down."
