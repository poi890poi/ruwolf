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
import datetime
import cgi
import json
import sqlite3
import sys
import uuid
import random

import logging
LOG_FILENAME = 'debug.log'
logging.basicConfig(filename=LOG_FILENAME,level=logging.DEBUG)

# init variables

INTERVAL_SHORT = 3 * 1000
INTERVAL_LONG = 30 * 1000
INTERVAL_DROPUSER = 12 * 60 * 1000
TIME_MAX = long(9999999999999)

# message types, specified in user column
SYSTEM_USER = 'aaedddbf-13a9-402b-8ab2-8b0073b3ebf3'
GUID_0 = '3e5cdec2-f504-4474-ba0f-2f358c210be8'
GUID_0 = '7051262e-c2ff-4e69-b2ed-76cb4d01eb9a'
GUID_0 = '87018045-fd87-4f7c-ad87-94b9c898cdfe'
GUID_0 = '4b89497a-2bb1-4234-9747-cd7c862479be'
GUID_0 = '9fe94f24-4e45-4cc6-b030-6363d2e7cc1f'
GUID_0 = '8f4c6b3e-0aa8-4d41-a550-95a8e7dd04e0'
GUID_0 = 'a745ee66-6538-48e2-97f1-9eaf32ce5701'
GUID_0 = '1df5fd0f-06eb-4961-a96e-27e78567eb98'
GUID_0 = 'ceb7d84e-f5c2-4f9b-9700-a1d3c63c771e'
GUID_0 = '204c4a4e-5b67-4745-b104-9f6dcf0ad8e4'

# message types
MSG_USER_STATUS = 1
MSG_ROOM = 2
MSG_USERQUIT = 3
MSG_USR_STA_PRIVATE = 4
MSG_USR_STA_ALIGNMENT = 5
MSG_GAMEDROP = 6
MSG_GAMEDROP_P = 7
MSG_ROOM_DETAIL = 8

# user status
USR_PUBLIC_MASK = 0x000000ff
USR_PRIVATE_MASK = 0x00ffff00

USR_CONN = 0x00000001
USR_SURVIVE = 0x00000002
USR_HOST = 0x00000004
USR_RDYCHK = 0x00000008
USR_KICKED = 0x00000010
USR_HANG = 0x00000020
USR_DEADLOCKED_E = 0x00000040

USR_PRESERVE = 0x00000080

USR_VOTE_LYNCH = 0x00000100
USR_VOTE_CASTING = 0x00000200

USR_PRESERVE = 0x00000400
USR_PRESERVE = 0x00000800

USR_VOTE_BITE = 0x00001000
USR_NA_BLOCK = 0x00002000
USR_NA_DETECT = 0x00004000
USR_NA_PROTECT = 0x00008000
USR_NA_AUTOPSY = 0x000010000
USR_NA_CUPID = 0x000020000

USR_PRESERVE = 0x000040000
USR_PRESERVE = 0x000080000

USR_D_TARGET1 = 0x000100000
USR_D_TARGET2 = 0x000200000
USR_D_TARGET3 = 0x000400000
USR_D_TARGET4 = 0x000800000

USR_VOTE_MASK = USR_RDYCHK | USR_VOTE_LYNCH | USR_VOTE_CASTING | \
    USR_VOTE_BITE | USR_NA_BLOCK | USR_NA_DETECT | USR_NA_PROTECT | \
    USR_NA_AUTOPSY | USR_NA_CUPID

# roles
ROLE_ALIGNMENT_SHIFT = 24

ROLE_VILLAGER = 0x00000000
ROLE_SEER = 0x00000001
ROLE_HEALER = 0x00000002
ROLE_HUNTER = 0x00000004
ROLE_PRESERVE = 0x00000008

ROLE_CUPID = 0x00000010
ROLE_LOVER = 0x00000020
ROLE_PRESERVE = 0x00000040
ROLE_PRESERVE = 0x00000080

ROLE_WOLF = 0x00000100
ROLE_BLOCKER = 0x00000200
ROLE_ALPHA_WOLF = 0x00000400
ROLE_MADMAN = 0x00000800
ROLE_JUNIOR_WOLF = 0x00001000
ROLE_PRESERVE = 0x00002000
ROLE_PRESERVE = 0x00004000
ROLE_PRESERVE = 0x00008000

# privileges
PVG_ALIGNMENT_MASK = 0xff0000000

PVG_ROOMCHAT = 0x00000001

PVG_DETECTOR1 = 0x000100000
PVG_DETECTOR2 = 0x000200000
PVG_DETECTOR3 = 0x000400000
PVG_DETECTOR4 = 0x000800000

PVG_PRIVATE = 0xffffffff

# do later actions
DLTR_COMMIT_DB = 0b00000001

do_later_short = long(0)
do_later_long = long(0)
do_later_mask = 0

user_activity = dict()
user_status = dict()

html_escape_table = {
    "&": "&amp;",
    '"': "&quot;",
    "'": "&#39",
    ">": "&gt;",
    "<": "&lt;",
    "=": "&#61",
    ",": "&#44;",
    #" ": "&nbsp;", # this causes line break problem
    "\n": "<br/>",
    }

# init database

appdata = os.path.join(os.environ['APPDATA'], u'MyPythonApp')
if not os.path.isdir(appdata):
    os.mkdir(appdata)
dbf = os.path.join(appdata, u'pychat.db')

conn = sqlite3.connect(dbf)

dbcursor = conn.cursor()

# Create table
dbcursor.execute('''create table if not exists message
(roomid text, timestamp integer, privilege integer, username text,
datetime text, message text, type integer, reserved1 integer, reserved2 text)''')

dbcursor.execute('''create table if not exists user
(username text, password text, sessionkey text, ip text, roomid text,
role integer, status integer, privilege integer, displayntable text,
lastactivity integer, reserved1 integer, reserved2 text)''')

dbcursor.execute('''create table if not exists room
(username text, roomid text, description text, ruleset integer, options integer,
phase integer, timeout integer, reserved1 integer, reserved2 text)''')

# System messages are cached in a queue.
# They are not saved in database.
# When clients request for new messages. It's sent to clients.
# Some types of system message have life spans.
# Such messages are cached in a set. So there's no duplicated entry with same name.

sys_msg = []

# class definition

def html_escape(text):
    """Produce entities within text."""
    return "".join(html_escape_table.get(c,c) for c in text)

def get_time_norm():
    return long(time.time()*1000)

def upd_room(roomid):
    dbcursor.execute("""delete from message where username=? and type=?""", (roomid, MSG_ROOM))
    dbcursor.execute("""select count(*) from user where roomid=? and status&?""", (roomid, USR_CONN))
    sqlcount = dbcursor.fetchall()
    user_count = sqlcount[0][0]
    if user_count == -1: user_count = 0
    rec = None
    dbcursor.execute("""select * from room where roomid=?""", (roomid,))
    rec = dbcursor.fetchone()
    logging.debug('user_count, room: '+roomid+', count: '+str(user_count))
    if rec:
        timestamp = get_time_norm()
        privilege = 0
        username = roomid
        participant = user_count
        json_serial = (rec[2], rec[3], rec[4], rec[5], rec[0], roomid, participant)
        message = json.dumps(json_serial)
        dbcursor.execute('insert into message values (?,?,?,?,?,?,?,?,?)', \
            ('', timestamp, 0, username, '', message, MSG_ROOM, 0, ''))
        logging.debug('upd_room, room: '+roomid+', json: '+message)

        dbcursor.execute('insert into message values (?,?,?,?,?,?,?,?,?)', \
            (roomid, timestamp, 0, username, '', message, MSG_ROOM_DETAIL, 0, ''))

def upd_user_status(user):
    global user_status
    dbcursor.execute("""delete from message where username=? and (type=? or type=? or type=?)""", \
        (user, MSG_USER_STATUS, MSG_USR_STA_PRIVATE, MSG_USR_STA_ALIGNMENT))
    rec = None
    dbcursor.execute("""select * from user where username=?""", (user,))
    rec = dbcursor.fetchone()
    print 'rec: ', rec
    if rec:
        roomid = rec[4]
        role = rec[5]
        timestamp = get_time_norm()
        privilege = 0
        username = user
        json_serial = (0, 0, 0, '')
        status = 0
        if user in user_status:
            status = user_status[user]

        # check if the user is a host
        status &= ~USR_HOST
        dbcursor.execute("""select * from room where roomid=?""", (roomid, ))
        room = dbcursor.fetchone()
        if room:
            if room[0] == username:
                status |= USR_HOST

        logging.debug('user_status: '+str(hex(status)))

        json_serial = (roomid, status&USR_PUBLIC_MASK, 0, user)
        message = json.dumps(json_serial)
        dbcursor.execute('insert into message values (?,?,?,?,?,?,?,?,?)', \
            (roomid, timestamp, 0, username, '', message, MSG_USER_STATUS, 0, ''))
        logging.debug('upd_user_status, public, user: '+user+', json: '+message)

        # settings for testing only
        alignment = 0x1
        alignment <<= ROLE_ALIGNMENT_SHIFT
        role = ROLE_WOLF | ROLE_BLOCKER
        privilege = alignment

        json_serial = (roomid, status, role, user)
        message = json.dumps(json_serial)
        dbcursor.execute('insert into message values (?,?,?,?,?,?,?,?,?)', \
            (roomid, timestamp+1, privilege, username, '', message, MSG_USR_STA_ALIGNMENT, 0, ''))
        logging.debug('upd_user_status, alignment, user: '+user+', json: '+message+', privilege: '+str(privilege))

        json_serial = (roomid, status, role, user)
        message = json.dumps(json_serial)
        dbcursor.execute('insert into message values (?,?,?,?,?,?,?,?,?)', \
            (roomid, timestamp+2, PVG_PRIVATE, username, '', message, MSG_USR_STA_PRIVATE, 0, ''))
        logging.debug('upd_user_status, private, user: '+user+', json: '+message+', privilege: '+str(PVG_PRIVATE))

        dbcursor.execute("""update user set status=? where username=?""", (status, user))
        user_status[user] = status

def msg_command(roomid, type, argument):
    now = time.time()
    timestamp = long(now*1000)
    ct = time.localtime(now)
    isoformat = datetime.time(ct.tm_hour,ct.tm_min,ct.tm_sec).isoformat()
    dbcursor.execute('insert into message values (?,?,?,?,?,?,?,?,?)', \
        (roomid, timestamp, 0, SYSTEM_USER, isoformat, argument, type, 0, ''))

def dbg_msg(message):
    now = time.time()
    timestamp = long(now*1000)
    ct = time.localtime(now)
    isoformat = datetime.time(ct.tm_hour,ct.tm_min,ct.tm_sec).isoformat()
    dbcursor.execute('insert into message values (?,?,?,?,?,?,?,?,?)', \
        ('', timestamp, 0, SYSTEM_USER, isoformat, message, 0, 0, ''))

def sys_msg(message, roomid):
    now = time.time()
    timestamp = long(now*1000)
    ct = time.localtime(now)
    isoformat = datetime.time(ct.tm_hour,ct.tm_min,ct.tm_sec).isoformat()
    dbcursor.execute('insert into message values (?,?,?,?,?,?,?,?,?)', \
        (roomid, timestamp, 0, SYSTEM_USER, isoformat, message, 0, 0, ''))

def check_dltr_mask(mask_bit):
    global do_later_mask
    ret = do_later_mask & mask_bit
    do_later_mask &= ~mask_bit
    return ret

def check_do_later():
    global do_later_short, do_later_long
    now = get_time_norm()
    print 'now: ', now
    print 'do_later_short: ', do_later_short
    if now > do_later_short:
        for user in user_status:
            if user_status[user] & USR_CONN:
                # check connected user for discon
                if user not in user_activity:
                    user_activity[user] = 0
                if now - user_activity[user] > INTERVAL_SHORT:
                    user_status[user] &= ~USR_CONN
                    upd_user_status(user)
                    logging.debug('user discon, user: '+user)

        do_later_short = now + INTERVAL_SHORT

    if now > do_later_long:
        # do something
        if check_dltr_mask(DLTR_COMMIT_DB):
            conn.commit()
            logging.debug('commit database')

        do_later_long = now + INTERVAL_LONG

class MyHandler(RequestHandler):
    def handle_get(self):
        self.path = 'html' + self.path
        print 'try ', self.path
        if not os.path.isfile(self.path):
            self.path = '/html/template.html'
            print 'else ', self.path
        RequestHandler.handle_data(self)

    def handle_post(self):
        global svr_doc_time, msg_cache, do_later_mask, \
            user_activity, user_status

        if self.path != '/check_update':
            logging.debug('post, command: '+self.path+', ip: '+self.client_address[0]+', value: '+self.rfile.getvalue())

        if self.path == '/login':
            login = unicode(self.rfile.getvalue(), 'utf-8')
            #login = self.rfile.getvalue()
            login = login.splitlines()
            print 'login: ', login
            username = u''
            password = u''
            if login[0]:
                username = login[0]
            if login[1]:
                password = login[1]
            print u'username: ', username
            print u'password: ', password

            sessionkey = None
            ip = self.client_address[0]

            dbcursor.execute("""select * from user where ip=?""", (ip,))
            conflict = dbcursor.fetchone()
            if conflict:
                logging.debug('double login, ip: '+ip+', user: '+username)

            dbcursor.execute("""select * from user where username=?""", (username,))
            auth = dbcursor.fetchone()
            if auth:
                print 'user exists'
                print auth
                if auth[1] == password:
                    print 'user login'
                    sessionkey = str(uuid.uuid4())
                    dbcursor.execute("""update user set sessionkey=?, ip=?, roomid=? where username=?""", (sessionkey, ip, '', username))
                    #do_later_mask |= DLTR_COMMIT_DB
                    conn.commit()
                else:
                    print 'incorrect password'
            else:
                print 'user register'
                sessionkey = str(uuid.uuid4())
                roomid = ''
                role = 0
                status = 0
                privilege = 0
                displayntable = ''
                lastactivity = get_time_norm()
                dbcursor.execute('insert into user values (?,?,?,?,?,?,?,?,?,?,?,?)', \
                    (username, password, sessionkey, ip, roomid, \
                    role, status, privilege, displayntable, lastactivity, 0, ''))
                #do_later_mask |= DLTR_COMMIT_DB
                conn.commit()

            print 'sessionkey: ', sessionkey

            if sessionkey:
                self.send_response(200)
                self.send_header(u'Content-type', u'text/plain')
                self.end_headers()
                ret = json.dumps((sessionkey,username))
                self.wfile.write(ret)
            else:
                self.send_response(401)
                self.end_headers()

        elif self.path == '/logout':
            sessionkey = self.rfile.getvalue()
            ip = self.client_address[0]
            dbcursor.execute("""select * from user where sessionkey=? and ip=?""", (sessionkey,ip))
            auth = dbcursor.fetchone()
            if auth:
                username = auth[0]
                user_status.pop(username)
                reset = str(uuid.uuid4())
                dbcursor.execute("""update user set sessionkey=?, ip=?, roomid=? where sessionkey=?""", (reset, reset, '', sessionkey))
                dbcursor.execute("""delete from message where username=? and (type=? or type=? or type=?)""", \
                    (username, MSG_USER_STATUS, MSG_USR_STA_PRIVATE, MSG_USR_STA_ALIGNMENT))
                #do_later_mask |= DLTR_COMMIT_DB
                conn.commit()
                msg_command(auth[4], MSG_USERQUIT, username)

            self.send_response(401)
            self.end_headers()

        elif self.path == '/host':
            auth = None
            if 'Authorization' in self.headers:
                sessionkey = self.headers['Authorization']
                dbcursor.execute("""select * from user where
                    sessionkey=? and ip=?""", (sessionkey,self.client_address[0]))
                auth = dbcursor.fetchone()

            if auth:
                roomid = str(uuid.uuid4())
                description = unicode(self.rfile.getvalue(), 'utf-8')
                if description == '[rnd]':
                    with open('gamename.txt') as hfile:
                        lst = hfile.readlines()
                        description = random.choice(lst).decode('utf-8')
                        description = description.replace('\n', '')
                if not description:
                    description = roomid
                description = html_escape(description)
                ruleset = 0
                options = 0
                phase = 0
                timeout = TIME_MAX
                dbcursor.execute('insert into room values (?,?,?,?,?,?,?,?,?)', \
                    (auth[0], roomid, description, ruleset, options, phase, timeout, 0, ''))
                dbcursor.execute("""update user set roomid=?, privilege=privilege|? where username=?""", \
                    (roomid, PVG_ROOMCHAT, auth[0]))

                timestamp = get_time_norm()
                privilege = 0
                username = roomid
                participant = 1
                json_serial = (description, ruleset, options, phase, auth[0], roomid, participant)
                message = json.dumps(json_serial)
                dbcursor.execute('insert into message values (?,?,?,?,?,?,?,?,?)', \
                    ('', timestamp, 0, username, '', message, MSG_ROOM, 0, ''))

                logging.debug('/host, room: '+roomid+', host: '+auth[0])
                #user_status[auth[0]] |= USR_HOST

                upd_room(roomid)
                upd_user_status(auth[0])
                do_later_mask |= DLTR_COMMIT_DB
                msg_command('', MSG_USERQUIT, auth[0])

                self.send_response(205)
                self.end_headers()
            else:
                self.send_response(401)
                self.end_headers()

        elif self.path == '/drop':
            auth = None
            room = None
            if 'Authorization' in self.headers:
                sessionkey = self.headers['Authorization']
                dbcursor.execute("""select * from user where
                    sessionkey=? and ip=?""", (sessionkey,self.client_address[0]))
                auth = dbcursor.fetchone()

            if auth:
                username = auth[0]
                roomid = auth[4]
                status = user_status[username]

                dbcursor.execute("""select * from room where roomid=?""", \
                    (roomid, ))
                room = dbcursor.fetchone()

                if room:
                    if room[0] == username:
                        dbcursor.execute("""delete from message where username=? and type=?""", (roomid, MSG_ROOM))
                        dbcursor.execute("""delete from room where roomid=?""", (roomid, ))

                        dbcursor.execute("""update user set roomid=?, privilege=privilege&? where username=?""", \
                            ('', ~PVG_ROOMCHAT, username))
                        #user_status[username] &= ~USR_HOST
                        upd_user_status(username)

                        msg_command(roomid, MSG_GAMEDROP_P, roomid)
                        msg_command('', MSG_GAMEDROP, roomid)

                        do_later_mask |= DLTR_COMMIT_DB

                        self.send_response(205)
                        self.end_headers()

        elif self.path == '/ready':
            auth = None
            room = None
            if 'Authorization' in self.headers:
                sessionkey = self.headers['Authorization']
                dbcursor.execute("""select * from user where
                    sessionkey=? and ip=?""", (sessionkey,self.client_address[0]))
                auth = dbcursor.fetchone()

            if auth:
                username = auth[0]
                roomid = auth[4]

                dbcursor.execute("""select * from room where roomid=?""", \
                    (roomid, ))
                room = dbcursor.fetchone()

                if room:
                    if room[0] == username:
                        if room[5] == 0:
                            """Enter phase 1(ready check). The match starts after everyone votes for someone.
                            This is to make sure everyone knows how the game proceeds.
                            """
                            dbcursor.execute("""update room set phase=1 where roomid=?""", (roomid, ))

                            dbcursor.execute("""select * from user where
                                roomid=?""", (roomid, ))
                            userlist = dbcursor.fetchall()
                            for row in userlist:
                                logging.debug('issue a USR_RDYCHK vote to user: '+row[0])
                                user_status[row[0]] |= USR_RDYCHK
                                upd_user_status(row[0])

                            sys_msg('Vote for someone to start the match.', roomid)
                        else:
                            dbcursor.execute("""update room set phase=0 where roomid=?""", (roomid, ))

                        upd_room(roomid)
                        do_later_mask |= DLTR_COMMIT_DB

            self.send_response(204)
            self.end_headers()

        elif self.path == '/vote_rdy':
            auth = None
            if 'Authorization' in self.headers:
                sessionkey = self.headers['Authorization']
                dbcursor.execute("""select * from user where
                    sessionkey=? and ip=?""", (sessionkey,self.client_address[0]))
                auth = dbcursor.fetchone()

            if auth:
                username = auth[0]
                roomid = auth[4]

                dbcursor.execute("""select * from room where roomid=?""", \
                    (roomid, ))
                room = dbcursor.fetchone()

                if room:
                    if user_status[username] & USR_VOTE_MASK:
                        targetname = self.rfile.getvalue().decode('utf-8')
                        dbcursor.execute("""select * from user where username=?""", (targetname, ))
                        target = dbcursor.fetchone()

                        sys_msg(username+' voted for '+targetname, roomid)

                        user_status[username] &= ~USR_VOTE_MASK
                        upd_user_status(username)

                self.send_response(204)
                self.end_headers()

        elif self.path == '/kick':
            auth = None
            if 'Authorization' in self.headers:
                sessionkey = self.headers['Authorization']
                dbcursor.execute("""select * from user where
                    sessionkey=? and ip=?""", (sessionkey,self.client_address[0]))
                auth = dbcursor.fetchone()

            if auth:
                username = auth[0]
                roomid = auth[4]
                if user_status[username] & USR_HOST:
                    targetname = self.rfile.getvalue().decode('utf-8')
                    dbcursor.execute("""select * from user where
                        username=? and roomid=?""", (targetname, roomid))
                    target = dbcursor.fetchone()
                    if target:
                        dbcursor.execute("""update user set roomid=?, privilege=privilege&? where username=?""", \
                            ('', ~PVG_ROOMCHAT, targetname))
                        user_status[targetname] |= USR_KICKED
                        upd_user_status(targetname)
                        upd_room(roomid)

                        msg_command(roomid, MSG_USERQUIT, targetname)

                        do_later_mask |= DLTR_COMMIT_DB

                        logging.debug('/kick/, username: '+targetname+', roomid: '+roomid)

                self.send_response(204)
                self.end_headers()

        elif self.path == '/drop_confirm':
            auth = None
            if 'Authorization' in self.headers:
                sessionkey = self.headers['Authorization']
                dbcursor.execute("""select * from user where
                    sessionkey=? and ip=?""", (sessionkey,self.client_address[0]))
                auth = dbcursor.fetchone()

            if auth:
                username = auth[0]
                user_status[username] &= ~USR_KICKED
                upd_user_status(username)
                do_later_mask |= DLTR_COMMIT_DB

                self.send_response(204)
                self.end_headers()
            else:
                self.send_response(401)
                self.end_headers()

        elif self.path == '/quit':
            auth = None
            if 'Authorization' in self.headers:
                sessionkey = self.headers['Authorization']
                dbcursor.execute("""select * from user where
                    sessionkey=? and ip=?""", (sessionkey,self.client_address[0]))
                auth = dbcursor.fetchone()

            if auth:
                msg_command(auth[4], MSG_USERQUIT, auth[0])
                dbcursor.execute("""update user set roomid=?, privilege=privilege&? where username=?""", \
                    ('', ~PVG_ROOMCHAT, auth[0]))
                upd_user_status(auth[0])
                do_later_mask |= DLTR_COMMIT_DB

                logging.debug('/quit/, username: '+auth[0]+', roomid: '+auth[4])
                upd_room(auth[4])

                self.send_response(205)
                self.end_headers()
            else:
                self.send_response(401)
                self.end_headers()

        elif self.path == '/join':
            auth = None
            if 'Authorization' in self.headers:
                sessionkey = self.headers['Authorization']
                dbcursor.execute("""select * from user where
                    sessionkey=? and ip=?""", (sessionkey,self.client_address[0]))
                auth = dbcursor.fetchone()

            rejected = True
            if auth:
                roomid = self.rfile.getvalue()

                dbcursor.execute("""select * from room where roomid=?""", \
                    (roomid, ))
                room = dbcursor.fetchone()

                if room:
                    if room[5] == 0:
                        msg_command(auth[4], MSG_USERQUIT, auth[0])
                        dbcursor.execute("""update user set roomid=?, privilege=privilege|? where username=?""", \
                            (roomid, PVG_ROOMCHAT, auth[0]))
                        upd_user_status(auth[0])
                        do_later_mask |= DLTR_COMMIT_DB

                        logging.debug('/join/, username: '+auth[0]+', roomid: '+roomid)
                        upd_room(roomid)

                        rejected = False
                        self.send_response(205)
                        self.end_headers()

            if rejected:
                self.send_response(401)
                self.end_headers()

        elif self.path == '/send_text':
            # auth
            auth = None
            if 'Authorization' in self.headers:
                sessionkey = self.headers['Authorization']
                dbcursor.execute("""select * from user where
                    sessionkey=? and ip=?""", (sessionkey,self.client_address[0]))
                auth = dbcursor.fetchone()

            # preprocess the message
            msgbody = unicode(self.rfile.getvalue(), 'utf-8')
            msgbody = html_escape(msgbody)
            #msgbody = msgbody.replace('\n', '<br/>')

            # append message
            # IP as author is for test only, should replace with user id
            # still, IP should be saved in message entity
            author = self.client_address[0]
            author = unicode(author, 'utf-8')

            now = time.time()
            type = 1 # json type identifier: message
            roomid = ''
            timestamp = long(now*1000)
            privilege = 0
            username = author
            ct = time.localtime(now)
            if auth:
                username = auth[0]
                roomid = auth[4]
                if roomid:
                    privilege |= PVG_ROOMCHAT
            isoformat = datetime.time(ct.tm_hour,ct.tm_min,ct.tm_sec).isoformat()
            message = msgbody

            dbcursor.execute('insert into message values (?,?,?,?,?,?,?,?,?)', \
                (roomid, timestamp, privilege, username, isoformat, message, 0, 0, ''))
            do_later_mask |= DLTR_COMMIT_DB
            #conn.commit()

            self.send_response(204)
            self.end_headers()

        elif self.path == '/check_update':
            auth = None
            if 'Authorization' in self.headers:
                sessionkey = self.headers['Authorization']
                ip = self.client_address[0]

                dbcursor.execute("""select * from user where
                    sessionkey=? and ip=?""", (sessionkey,ip))
                auth = dbcursor.fetchone()
                print auth
                #time.sleep(100)

                if auth:
                    user_activity[auth[0]] = get_time_norm()
                    if auth[0] not in user_status:
                        user_status[auth[0]] = 0
                    if not user_status[auth[0]] & USR_CONN:
                        # user connected
                        user_status[auth[0]] |= USR_CONN
                        upd_user_status(auth[0])
                        logging.debug('user connected, user: '+auth[0])

            #print 'client document time: ', self.rfile.getvalue()
            client_doc_time = long(self.rfile.getvalue())
            #print 'client document time: ', client_doc_time
            #print 'type: ', type(float(client_doc_time))

            # query message
            roomid = ''
            privilege = 0
            username = ''
            if auth:
                username = auth[0]
                roomid = auth[4]
                privilege = auth[7]

            dbcursor.execute("""select * from message \
                where timestamp>? and roomid=? and ((privilege&?=privilege) or (type=? and username=?))""", \
                (client_doc_time, roomid, privilege, MSG_USR_STA_PRIVATE, username))
            json_serial = []
            for row in dbcursor:
                timestamp = row[1]
                author = row[3]
                isoformat = row[4]
                message = row[5]
                type = row[6]
                row_serial = (type, author, isoformat, message, timestamp)
                json_serial.append(row_serial)

            if json_serial:
                ret = json.dumps(json_serial)

                #logging.debug('/check_update, username: '+username+', content: '+ret)

                self.send_response(200)
                self.send_header(u'Content-type', u'text/plain')
                self.end_headers()
                self.wfile.write(ret)
            elif auth:
                self.send_response(204)
                self.end_headers()
            else:
                self.send_response(401)
                self.end_headers()

            check_do_later()

    def handle_data(self):
        if self.command == 'GET':
            self.handle_get()
        elif self.command == 'POST':
            self.handle_post()

if __name__=="__main__":
    # launch the server on the specified port
    now = get_time_norm()
    do_later_short = now + INTERVAL_SHORT
    do_later_long = now + INTERVAL_LONG

    # clear temp states
    dbcursor.execute("""delete from message where type=? or type=? or type=?""", \
        (MSG_USER_STATUS, MSG_USR_STA_PRIVATE, MSG_USR_STA_ALIGNMENT))

    port = 80
    s = Server('', port, MyHandler)
    print "SimpleAsyncHTTPServer running on port %s" % port
    try:
        asyncore.loop(timeout=2)
    except KeyboardInterrupt:
        conn.commit()
        dbconn.close()
        print "Crtl+C pressed. Shutting down."
