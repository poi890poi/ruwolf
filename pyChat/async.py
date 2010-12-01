﻿import os
import time
import datetime
import cgi
import json
import sqlite3
import sys
import uuid
import random

from recipe440665 import *
from constant import *

import logging
LOG_FILENAME = 'debug.log'
logging.basicConfig(filename=LOG_FILENAME,level=logging.DEBUG)

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

dbcursor.execute('''create table if not exists action
(roomid text, action integer, username text, target text, timestamp integer)''')

# class definition

def html_escape(text):
    """Produce entities within text."""
    return "".join(html_escape_table.get(c,c) for c in text)

def get_time_norm():
    """Timestamp is always integer, in miliseconds,
        to prevent float point precision problem
    """
    return long(time.time()*1000)

def upd_room(roomid):
    """Room status is a special message type with a single instance per room.
    Later status overwrites earlier one.
    """
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
    """User status are special message types.
    There are 3 types of them, each has a single instance per user.
        1. public user status
            Everyone in the room can see. Such as connection, surviving...
        2. alignment status
            Only players share the same alignments can see. Such as werewolf...
        3. private status
            Only the sole player can see. Such as seer...
    The 3 types must be updated the same time with a strict timestamp order.
        Private > Alignment > Public
    And alignment status always include public staus, private status always include alignment status.
    So player always get the full information that is avaliable for him.
    """
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

def private_msg(username, message, roomid):
    now = time.time()
    timestamp = long(now*1000)
    ct = time.localtime(now)
    isoformat = datetime.time(ct.tm_hour,ct.tm_min,ct.tm_sec).isoformat()
    dbcursor.execute('insert into message values (?,?,?,?,?,?,?,?,?)', \
        (roomid, timestamp, 0, username, isoformat, message, MSG_PRIVATE, 0, ''))

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

def check_vote(roomid):
    dbcursor.execute("""select count(*) from user where roomid=? and status&? and status&?""", \
        (roomid, USR_CONN, USR_ACT_MASK))
    sqlcount = dbcursor.fetchall()
    user_count = sqlcount[0][0]
    if user_count == -1:
        user_count = 0
    if user_count == 0:
        # all actions are taken

        dbcursor.execute("""select * from action where roomid=? and action=?""", \
            (roomid, ACT_VOTE_RDY))

        voter = dict()
        timestamp = dict()
        for rec in dbcursor:
            action = rec[1]
            username = rec[2]
            target = rec[3]
            if target not in voter:
                voter[target] = set()
            voter[target].add(username)
            if target not in timestamp:
                timestamp[target] = 0
            if rec[4] > timestamp[target]:
                timestamp[target] = rec[4]

        msg = ''
        max = 0
        elected = dict()
        for key, value in sorted(voter.iteritems(), key=lambda (k,v): (len(v)), reverse=True):
            if len(value) > max:
                max = len(value)
            if len(value) == max:
                elected[key] = timestamp[key]
            msg += key
            msg += ': '
            msg += str(len(value))
            if value:
                msg += ' ('
                list = ''
                for voter in value:
                    list += ', '
                    list += voter
                msg += list.replace(', ', '', 1)
                msg += ')<br/>'

        msg += '<br/>'

        final = ''
        if len(elected) > 1:
            # deadlocked election
            # USR_DEADLOCKED_E
            for key, value in sorted(elected.iteritems(), key=lambda (k,v): (v)):
                final = key
                break
                #msg += key + ' ' + str(value) + '<br/>'
        else:
            final = random.choice(elected.items())[0]

        msg += '<b>'
        msg += final
        msg += '</b>'
        msg += ' is hanged<br/>'

        sys_msg(msg, roomid)


    logging.debug('not voted yet: '+str(user_count))

def get_day_night(phase):
    """Phase is defined in hex.
    0x00-0x0f: Pre-match phase.
        0x00: Room is open for joining.
        0x01: The host has sent ready cehck. The room is cloesd and the match starts after every voted.
    0x0010-0xffff: Game is commencing.
        Each phase is divided to 0xf sub-phases.
    0x10000-0xfffff: The game ended.
    Return values:
        -1: game not commencing, 0: day, 1: night
    """
    if (phase >> 4 == 0) or phase > 0xffff:
        return -1
    return (phase >> 4) % 2

def get_subphase(phase):
    """Sub-phases definition:
        0x0-0x5: Pre-election phases.
        ox6: First round election.
        0x7-0x9: Second round elections.
        0x-0xf: Post-election phases.
    """
    return phase & 0xf

def phase_advance(phase):
    reurn ((phase >> 4) + 0x1) << 4

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

            self.send_response(205)
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
                username = auth[0]
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
                    (username, roomid, description, ruleset, options, phase, timeout, 0, ''))
                dbcursor.execute("""update user set roomid=?, privilege=privilege|? where username=?""", \
                    (roomid, PVG_ROOMCHAT, username))

                timestamp = get_time_norm()
                privilege = 0
                participant = 1
                json_serial = (description, ruleset, options, phase, username, roomid, participant)
                message = json.dumps(json_serial)
                dbcursor.execute('insert into message values (?,?,?,?,?,?,?,?,?)', \
                    ('', timestamp, 0, roomid, '', message, MSG_ROOM, 0, ''))

                sys_msg('Welcome to <b>'+description+'</b> hosted by '+username+'.', roomid)
                logging.debug('/host, room: '+roomid+', host: '+username)
                #user_status[username] |= USR_HOST

                upd_room(roomid)
                upd_user_status(username)
                do_later_mask |= DLTR_COMMIT_DB
                msg_command('', MSG_USERQUIT, username)

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
                        dbcursor.execute("""select * from user where
                            roomid=?""", (roomid, ))
                        userlist = dbcursor.fetchall()
                        if room[5] == 0:
                            """Enter phase 1(ready check). The match starts after everyone votes for someone.
                            This is to make sure everyone knows how the game proceeds.
                            """
                            dbcursor.execute("""update room set phase=1 where roomid=?""", (roomid, ))
                            dbcursor.execute("""delete from action where roomid=?""", (roomid, ))
                            for row in userlist:
                                logging.debug('issue a USR_DAY_VOTE vote to user: '+row[0])
                                user_status[row[0]] |= USR_DAY_VOTE
                                upd_user_status(row[0])

                            sys_msg('Vote for someone to start the match.', roomid)
                        else:
                            dbcursor.execute("""update room set phase=0 where roomid=?""", (roomid, ))
                            dbcursor.execute("""delete from action where roomid=?""", (roomid, ))
                            for row in userlist:
                                logging.debug('remove USR_DAY_VOTE vote from user: '+row[0])
                                user_status[row[0]] &= ~USR_DAY_VOTE
                                upd_user_status(row[0])

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
                    if user_status[username] & USR_ACT_MASK:
                        targetname = self.rfile.getvalue().decode('utf-8')
                        dbcursor.execute("""select * from user where roomid=? and username=?""", (roomid, targetname, ))
                        target = dbcursor.fetchone()

                        if target:
                            #sys_msg(username+' voted for '+targetname, roomid)
                            user_status[username] &= ~USR_ACT_MASK
                            upd_user_status(username)

                            dbcursor.execute('insert into action values (?,?,?,?,?)', \
                                (roomid, ACT_VOTE_RDY, username, targetname, get_time_norm()))
                            check_vote(roomid)

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
                    phase = room[5]
                    if phase == 0:
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

                dbcursor.execute("""select * from room where roomid=?""", (roomid, ))
                room = dbcursor.fetchone()

                if room:
                    phase = room[5]
                    if phase < 10:
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
                where timestamp>? and roomid=? and ((privilege&?=privilege) or ((type=? or type=?) and username=?))""", \
                (client_doc_time, roomid, privilege, MSG_USR_STA_PRIVATE, MSG_PRIVATE, username))
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