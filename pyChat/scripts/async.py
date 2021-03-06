﻿import os
import time
import datetime
import cgi
import json
import sqlite3
import sys
import uuid
import random
import hashlib
import logging
import logging.handlers

#from recipe440665 import *
from asynchttp import *
from constant import *
from function import *
from lang import *

appdata = os.path.join(os.environ['APPDATA'], APPDATA_FOLDER)
appdata = u'userdata'
if not os.path.isdir(appdata):
    os.mkdir(appdata)

logf = os.path.join(appdata, u'_debug.log')

# Set up a specific logger with our desired output level
my_logger = logging.getLogger('MyLogger')
my_logger.setLevel(logging.DEBUG)

# Add the log message handler to the logger
handler = logging.handlers.RotatingFileHandler(
              logf, maxBytes=262144, backupCount=10)

# create formatter
formatter = logging.Formatter("%(asctime)s - %(lineno)s - %(levelname)s - %(message)s")

# add formatter to ch
handler.setFormatter(formatter)

my_logger.addHandler(handler)

do_later_short = long(0)
do_later_long = long(0)
do_later_mask = 0

user_activity = dict()
user_status = dict()
user_role = dict()

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

dbf = os.path.join(appdata, DB_FILENAME)
conn = sqlite3.connect(dbf)
dbcursor = conn.cursor()
dbcomitted = 0

rndtable256 = []

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
    MSG_ROOM is post in lobby
    MSG_ROOM_DETAIL is post in private room
    """
    global do_later_mask
    dbcursor.execute("""delete from message where username=? and (type=? or type=?)""", (roomid, MSG_ROOM, MSG_ROOM_DETAIL))
    dbcursor.execute("""select count(*) from user where roomid=? and status&?""", (roomid, USR_CONN) )
    sqlcount = dbcursor.fetchall()
    user_count = sqlcount[0][0]
    if user_count == -1: user_count = 0
    rec = None
    dbcursor.execute("""select * from room where roomid=?""", (roomid,))
    rec = dbcursor.fetchone()
    #my_logger.debug('user_count, room: '+roomid+', count: '+str(user_count))
    if rec:
        timestamp = get_time_norm()
        privilege = 0
        username = roomid
        participant = user_count
        roommessage = rec[7]
        
        host = rec[0]
        dbcursor.execute("""select * from user where username=?""", (rec[0],) )
        auth = dbcursor.fetchone()
        if auth:
            if auth[9]:
                host = auth[9]
            elif rec[10]:
                host = auth[10]
            
        json_serial = (rec[2], rec[3], rec[4], rec[5], host, roomid, participant, html_escape(roommessage) )
        message = json.dumps(json_serial)
        dbcursor.execute('insert into message values (?,?,?,?,?,?,?,?,?,?,?,?)', \
            ('', timestamp, 0, username, '', message, MSG_ROOM, 0, '', username, 0, ''))
        dbcursor.execute('insert into message values (?,?,?,?,?,?,?,?,?,?,?,?)', \
            (roomid, timestamp, 0, username, '', message, MSG_ROOM_DETAIL, 0, '', username, 0, ''))
        my_logger.debug('upd_room, room: '+roomid+', json: '+message)
    do_later_mask |= DLTR_COMMIT_DB

def upd_room_ingame(roomid):
    """When game is comencing, lobby no longer receives room status.
    Room status is only post in private room.
    """
    global do_later_mask
    dbcursor.execute("""delete from message where username=? and (type=? or type=?)""", (roomid, MSG_ROOM, MSG_ROOM_DETAIL))

    dbcursor.execute("""select count(*) from user where roomid=?""", (roomid, ))
    sqlcount = dbcursor.fetchall()
    user_count = sqlcount[0][0]
    if user_count == -1: user_count = 0

    dbcursor.execute("""select * from room where roomid=?""", (roomid,))
    rec = dbcursor.fetchone()
    if rec:
        timestamp = get_time_norm()
        privilege = 0
        username = roomid
        roommessage = rec[7]
        json_serial = (rec[2], rec[3], rec[4], rec[5], rec[0], roomid, user_count, roommessage)
        message = json.dumps(json_serial)

        dbcursor.execute('insert into message values (?,?,?,?,?,?,?,?,?,?,?,?)', \
            (roomid, timestamp, 0, username, '', message, MSG_ROOM_DETAIL, 0, '', username, 0, ''))
        my_logger.debug('upd_room_ingame, room: '+roomid+', json: '+message)
    do_later_mask |= DLTR_COMMIT_DB

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
    global user_status, user_role, do_later_mask, rndtable256
    dbcursor.execute("""delete from message where username=? and (type=? or type=? or type=? or type=?)""", \
        (user, MSG_USER_STATUS, MSG_USR_STA_PRIVATE, MSG_USR_STA_ALIGNMENT, MSG_SEER_RESULT))
    rec = None
    dbcursor.execute("""select * from user where username=?""", (user,))
    rec = dbcursor.fetchone()
    print 'rec: ', rec
    if rec:
        ip = rec[3]
        roomid = rec[4]
        role = rec[5]
        displayname = rec[9]
        email = rec[10]
        hashname = rec[11]

        my_logger.debug('ip: '+str(ip>>24)+'.'+str((ip&0xff0000)>>16)+'.'+str((ip&0xff00)>>8)+'.'+str(ip&0xff))
        maskip = str(rndtable256[ip>>24]) + '.' + \
            str(rndtable256[(ip&0xff0000)>>16]) + '.' + \
            str(rndtable256[(ip&0xff00)>>8]) + '.' + \
            str(rndtable256[ip&0xff])

        timestamp = get_time_norm()
        privilege = 0
        username = user
        json_serial = (0, 0, 0, '')
        status = 0
        if user in user_status:
            status = user_status[user]
        if user in user_role:
            role = user_role[user]

        # check if the user is a host
        status &= ~USR_HOST
        dbcursor.execute("""select * from room where roomid=?""", (roomid, ))
        room = dbcursor.fetchone()
        if room:
            if room[0] == username:
                status |= USR_HOST

            phase = room[5]
            daynight = get_day_night(phase)
            if daynight == -1:
                role = ROLE_VILLAGER
            else:
                maskip = ''
                email = ''

        my_logger.debug('user_status: '+hex(status))

        # public information
        json_serial = (roomid, status&USR_PUBLIC_MASK, 0, user, maskip, hashname, email, displayname)
        message = json.dumps(json_serial)
        dbcursor.execute('insert into message values (?,?,?,?,?,?,?,?,?,?,?,?)', \
            (roomid, timestamp, 0, username, '', message, MSG_USER_STATUS, 0, '', '[dsp]', 0, ''))
        my_logger.debug('upd_user_status, public, user: '+user+', json: '+message)

        # alignment information
        alignment = role >> ROLE_ALIGNMENT_SHIFT
        if alignment:
            my_logger.debug('role: '+hex(role))
            my_logger.debug('PVG_ALIGNMENT_MASK: '+hex(PVG_ALIGNMENT_MASK))
            privilege = role & PVG_ALIGNMENT_MASK
            json_serial = (roomid, status&USR_PUBLIC_MASK, role, user, maskip, hashname, email, displayname)
            message = json.dumps(json_serial)
            dbcursor.execute('insert into message values (?,?,?,?,?,?,?,?,?,?,?,?)', \
                (roomid, timestamp+1, privilege, username, '', message, MSG_USR_STA_ALIGNMENT, 0, '', '[dsp]', 0, ''))
            my_logger.debug('upd_user_status, alignment, user: '+user+', json: '+message+', privilege: '+hex(privilege))

        # information for seer
        # assume there's only one seer, temporarily
        if status & USR_DETECTED_MASK:
            dbcursor.execute("""select * from user where roomid=? and role&?=?""", (roomid, ~PVG_ALIGNMENT_MASK, ROLE_SEER))
            seer = dbcursor.fetchone()
            if seer:
                my_logger.debug('detection, seer: '+seer[0]+', target: '+user+', role: '+hex(role))
                seer_result = ROLE_VILLAGER
                if role & PVG_ALIGNMENT_MASK:
                    seer_result = ROLE_WOLF
                json_serial = (roomid, status&USR_PUBLIC_MASK, seer_result, user, maskip, hashname, email, displayname)
                message = json.dumps(json_serial)
                dbcursor.execute('insert into message values (?,?,?,?,?,?,?,?,?,?,?,?)', \
                    (roomid, timestamp+1, PVG_PRIVATE, username, '', message, MSG_SEER_RESULT, 0, seer[0], '[dsp]', 0, ''))
                my_logger.debug('upd_user_status, seer, user: '+seer[0]+', json: '+message+', privilege: '+hex(PVG_PRIVATE))

        # private information
        json_serial = (roomid, status, role, user, maskip, hashname, email, displayname)
        message = json.dumps(json_serial)
        dbcursor.execute('insert into message values (?,?,?,?,?,?,?,?,?,?,?,?)', \
            (roomid, timestamp+2, PVG_PRIVATE, username, '', message, MSG_USR_STA_PRIVATE, 0, username, '[dsp]', 0, ''))
        my_logger.debug('upd_user_status, private, user: '+user+', json: '+message+', privilege: '+hex(PVG_PRIVATE))

        # privilege setup should only be done at game_start
        # put here temporarily for easy coding
        privilege = 0
        if room:
            #username = room[0]
            #description = room[2]
            #ruleset = room[3]
            options = room[4]
            phase = room[5]
            timeout = room[6]
            #message = room[7]

            if status&USR_SURVIVE:
                privilege |= PVG_DAYCHAT
                daynight = get_day_night(phase)
                if daynight == 0: # day
                    pass
                elif daynight == 1: # night
                    pass
                else:
                    privilege |= PVG_ROOMCHAT
                privilege |= (role & PVG_ALIGNMENT_MASK)
                if alignment:
                    privilege |= PVG_NIGHTCHAT
            else:
                privilege |= PVG_ROOMCHAT
            if phase == PHS_AFTERMATH:
                privilege = PVG_AFTERMATH

        dbcursor.execute("""update user set status=?, role=?, privilege=?
            where username=?""", (status, role, privilege, user))
        user_status[user] = status
    do_later_mask |= DLTR_COMMIT_DB

def msg_onetime(roomid, username, type, argument):
    # used for private message exclusively, as it's deleted immediately after being fetched
    now = time.time()
    timestamp = long(now*1000)
    ct = time.localtime(now)
    isoformat = datetime.time(ct.tm_hour,ct.tm_min,ct.tm_sec).isoformat()
    dbcursor.execute('insert into message values (?,?,?,?,?,?,?,?,?,?,?,?)', \
        (roomid, timestamp, PVG_PRIVATE, username, isoformat, argument, type, 0, username, '[dsp]', 0, ''))
    my_logger.debug('msg_onetime, type: %s, username: %s' % (hex(type), username))

def msg_command(roomid, type, argument):
    now = time.time()
    timestamp = long(now*1000)
    ct = time.localtime(now)
    isoformat = datetime.time(ct.tm_hour,ct.tm_min,ct.tm_sec).isoformat()
    dbcursor.execute('insert into message values (?,?,?,?,?,?,?,?,?,?,?,?)', \
        (roomid, timestamp, 0, SYSTEM_USER, isoformat, argument, type, 0, '', SYSTEM_USER, 0, ''))
    my_logger.debug('msg_command, type: %s, argument: %s' % (hex(type), argument))

def dbg_msg(message):
    now = time.time()
    timestamp = long(now*1000)
    ct = time.localtime(now)
    isoformat = datetime.time(ct.tm_hour,ct.tm_min,ct.tm_sec).isoformat()
    dbcursor.execute('insert into message values (?,?,?,?,?,?,?,?,?,?,?,?)', \
        ('', timestamp, 0, SYSTEM_USER, isoformat, message, 0, 0, '', SYSTEM_USER, 0, ''))

def sys_msg(message, roomid, phase = 0):
    my_logger.debug('sys_msg: '+message)

    now = time.time()
    timestamp = long(now*1000)
    ct = time.localtime(now)
    isoformat = datetime.time(ct.tm_hour,ct.tm_min,ct.tm_sec).isoformat()

    privilege = 0
    dbcursor.execute("""select * from room where roomid=?""", (roomid, ))
    room = dbcursor.fetchone()
    if room:
        phase = room[5]
        my_logger.debug('phase: '+hex(phase))
        daynight = get_day_night(phase)
        my_logger.debug('daynight: '+str(daynight))
        if daynight == 0: # day
            privilege |= PVG_DAYCHAT
        elif daynight == 1: # night
            privilege |= PVG_DAYCHAT
        else:
            privilege |= PVG_ROOMCHAT

    dbcursor.execute('insert into message values (?,?,?,?,?,?,?,?,?,?,?,?)', \
        (roomid, timestamp, privilege, SYSTEM_USER, isoformat, message, 0, phase, '', SYSTEM_USER, 0, ''))

def report_msg(message, roomid, phase = 0):
    my_logger.debug('sys_msg: '+message)

    now = time.time()
    timestamp = long(now*1000)
    ct = time.localtime(now)
    isoformat = datetime.time(ct.tm_hour,ct.tm_min,ct.tm_sec).isoformat()

    dbcursor.execute("""select * from delaymsg where roomid=?""", (roomid, ))
    exist = dbcursor.fetchone()
    if exist:
        message = exist[5] + message + '<br/>'

    dbcursor.execute("""delete from delaymsg where roomid=?""", (roomid, ))

    privilege = 0
    dbcursor.execute("""select * from room where roomid=?""", (roomid, ))
    room = dbcursor.fetchone()
    if room:
        phase = room[5]
        my_logger.debug('phase: '+hex(phase))
        daynight = get_day_night(phase)
        my_logger.debug('daynight: '+str(daynight))
        if daynight == 0: # day
            privilege |= PVG_DAYCHAT
        elif daynight == 1: # night
            privilege |= PVG_DAYCHAT
        else:
            privilege |= PVG_ROOMCHAT

    dbcursor.execute('insert into delaymsg values (?,?,?,?,?,?,?,?,?,?,?,?)', \
        (roomid, timestamp, privilege, SYSTEM_USER, isoformat, message, 0, phase, '', SYSTEM_USER, 0, ''))

def report_msg_commit(roomid, phase = 0):
    now = time.time()
    timestamp = long(now*1000)
    ct = time.localtime(now)
    isoformat = datetime.time(ct.tm_hour,ct.tm_min,ct.tm_sec).isoformat()

    dbcursor.execute("""select * from delaymsg where roomid=?""", (roomid, ))
    exist = dbcursor.fetchone()
    if exist:
        my_logger.debug('report_msg_commit: '+exist[5])
        sys_msg(exist[5], roomid, phase)

    dbcursor.execute("""delete from delaymsg where roomid=?""", (roomid, ))

def private_msg(username, message, roomid, phase):
    now = time.time()
    timestamp = long(now*1000)
    ct = time.localtime(now)
    isoformat = datetime.time(ct.tm_hour,ct.tm_min,ct.tm_sec).isoformat()
    dbcursor.execute('insert into message values (?,?,?,?,?,?,?,?,?,?,?,?)', \
        (roomid, timestamp, PVG_PRIVATE, username, isoformat, message, MSG_PRIVATE, phase, username, '[dsp]', 0, ''))

def check_dltr_mask(mask_bit):
    global do_later_mask
    ret = do_later_mask & mask_bit
    do_later_mask &= ~mask_bit
    return ret

def check_do_later():
    global do_later_short, do_later_long, dbcomitted
    now = get_time_norm()
    #print 'now: ', now
    #print 'do_later_short: ', do_later_short
    if now > do_later_short:
        # check user disconnection
        for user in user_status:
            if user_status[user] & USR_CONN:
                # check connected user for discon
                if user not in user_activity:
                    user_activity[user] = 0
                if now - user_activity[user] > INTERVAL_SHORT:
                    user_status[user] &= ~USR_CONN
                    upd_user_status(user)
                    my_logger.debug('user discon, user: '+user)

        # check room timeout
        dbcursor.execute("""select * from room where timeout<=?""", \
            (now,))
        roomlist = dbcursor.fetchall()
        for room in roomlist:
            process_timeout(room)

        do_later_short = now + INTERVAL_SHORT

    if now > do_later_long:
        # commit database
        if conn.total_changes > dbcomitted:
            conn.commit()
            my_logger.debug('commit database, '+str(conn.total_changes-dbcomitted))
            dbcomitted = conn.total_changes

        # check ended games
        #dbcursor.execute("""select * from room where phase >= ?""", \
        #    (0xffff,))
        # any empty room should be archived, whether it's finished or not
        dbcursor.execute("""select * from room""")
        roomlist = dbcursor.fetchall()
        for room in roomlist:
            roomid = room[1]
            description = room[2]
            ruleset = room[3]
            options = room[4]
            phase = room[5]
            timeout = room[6]
            message = room[7]

            dbcursor.execute("""select count(*) from user where roomid=? and status&?""", (roomid, USR_CONN) )
            sqlcount = dbcursor.fetchall()
            user_count = sqlcount[0][0]
            if user_count == -1 or user_count == 0:
                dbcursor.execute("""select * from message where roomid=? order by timestamp desc limit 1""", \
                    (roomid,))
                lastmsg = dbcursor.fetchone()
                archive = False;
                now = 0
                timestamp = 0
                if lastmsg:
                    timestamp = lastmsg[1]
                    now = get_time_norm()
                    if now-timestamp > INTERVAL_ARCHIVE:
                        archive = True;
                else:
                    archive = True;
                if archive:
                    dbcursor.execute("""delete from message where username=? and (type=? or type=?)""", (roomid, MSG_ROOM, MSG_ROOM_DETAIL))
                    dbcursor.execute("""select * from user where roomid = ?""", \
                        (roomid,) )
                    userlist = dbcursor.fetchall()
                    for user in userlist:
                        msg_command(user[4], MSG_USERQUIT, user[11])
                        dbcursor.execute("""update user set roomid=?, privilege=? where username=?""", \
                            ('', 0, user[0]))
                        upd_user_status(user[0])
                    msg_command(roomid, MSG_GAMEDROP_P, roomid)
                    msg_command('', MSG_GAMEDROP, roomid)
                    # to do: actually archive messages and room entry
                    dbcursor.execute("""delete from room where roomid=?""", (roomid,) )
                    my_logger.debug('archive, roomid: %s, silent: %d' % (roomid,now-timestamp) )
        
        # check idle users
        dbcursor.execute("""select * from user where lastactivity < ? and status&?=0""", \
            (now-INTERVAL_DROPUSER, USR_CONN) )
        userlist = dbcursor.fetchall()
        for user in userlist:
            # user idle for too long
            username = user[0]
            roomid = user[4]
            lastactivity = user[8]
            hashname = user[11]
            dbcursor.execute("""delete from message where username=? and (type=? or type=? or type=? or type=?)""", \
                (username, MSG_USER_STATUS, MSG_USR_STA_PRIVATE, MSG_USR_STA_ALIGNMENT, MSG_SEER_RESULT) )
            if username in user_status:
                user_status.pop(username)
            msg_command(roomid, MSG_USERQUIT, hashname)
            my_logger.debug('drop user, username: %s, lastactivity: %d' % (username,lastactivity) )

        do_later_long = now + INTERVAL_LONG
        
def safe_user_status(username):
    """Prevent KeyError when accessing user_status[username]
    """
    if username in user_status:
        pass
    else:
        dbcursor.execute("""select * from user where username=?""", (username, ))
        user = dbcursor.fetchone()
        if user:
            print 'user: ', user
            user_status[user[0]] = user[6]
            scan_ip_conflict()
            upd_user_status(user[0])
    

def process_timeout(room):
    roomid = room[1]
    description = room[2]
    ruleset = room[3]
    options = room[4]
    phase = room[5]
    timeout = room[6]
    message = room[7]

    my_logger.debug('process timeout, roomid: %s, timeout: %d, now: %d, phase: %s' % (roomid,timeout,get_time_norm(),hex(phase)) )

    # check untaken actions
    dbcursor.execute("""select * from user where roomid=? and status&?""", \
        (roomid, USR_ACT_MASK))
    userlist = dbcursor.fetchall()
    for user in userlist:
        username = user[0]
        role = user[5]
        safe_user_status(username)
        status = user_status[username]
        # to-do: check specific actions and process one by one
        user_status[username] &= ~USR_ACT_MASK
        upd_user_status(username)
    check_vote(room)

    if phase >= PHS_AFTERMATH:
        dbcursor.execute("""update room set timeout=? where roomid=?""", \
            (TIME_MAX, roomid))

def get_string(rid, locale='cht'):
    if isinstance(lang[locale][rid], tuple):
        return random.choice(lang[locale][rid])
    return lang[locale][rid]

def kill_player(room, username, lynch = False):
    global user_status

    roomid = room[1]
    options = room[4]
    phase = room[5]

    dbcursor.execute("""select * from user where roomid=? and username=? and status&?""", \
        (roomid, username, USR_SURVIVE))
    victim = dbcursor.fetchone()
    if victim:
        user_status[username] &= ~USR_SURVIVE
        user_status[username] &= ~USR_ACT_MASK
        if lynch:
            user_status[username] |= USR_LYNCH
            my_logger.debug('lynched, user: '+username)
        my_logger.debug('status: '+hex(user_status[username]))
        upd_user_status(username)
        msg_onetime(roomid, username, MSG_RELOAD, '')
        private_msg(username, get_string('sys_dead'), roomid, 0)

def check_game_end(room):
    global user_status

    roomid = room[1]
    options = room[4]
    phase = room[5]

    is_end = False

    dbcursor.execute("""select count(*) from user where roomid=? and status&?""", \
        (roomid, USR_SURVIVE))
    sqlcount = dbcursor.fetchall()
    survive_cnt = sqlcount[0][0]
    if survive_cnt == -1:
        survive_cnt = 0

    dbcursor.execute("""select count(*) from user where roomid=? and status&? and role&?""", \
        (roomid, USR_SURVIVE, PVG_ALIGNMENT_MASK))
    sqlcount = dbcursor.fetchall()
    wolf_cnt = sqlcount[0][0]
    if wolf_cnt == -1:
        wolf_cnt = 0

    if wolf_cnt == 0:
        msg = get_string('sys_villager_win')
        sys_msg(msg, roomid, phase)
        is_end = True
    elif wolf_cnt > survive_cnt/2:
        msg = get_string('sys_wolf_win')
        sys_msg(msg, roomid, phase)
        is_end = True

    if is_end:
        report_msg_commit(roomid, phase)
        dbcursor.execute("""update room set timeout=? where roomid=?""", \
            (TIME_MAX, roomid))
        pass

    return is_end
    
def get_displayname(roomid, username):
    dbcursor.execute("""select * from user where roomid=? and username=?""", \
        (roomid, username))
    rec = dbcursor.fetchone()
    if rec:
        return rec[9]
    return '[err]'

def check_vote_day(room):
    roomid = room[1]
    options = room[4]
    phase = room[5]

    dbcursor.execute("""select * from action where roomid=? and action=?""", \
        (roomid, USR_DAY_VOTE))

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

    my_logger.debug('voter: '+repr(voter))

    msg = u''
    max = 0
    elected = dict()
    for key, value in sorted(voter.iteritems(), key=lambda (k,v): (len(v)), reverse=True):
        if len(value) > max:
            max = len(value)
        if len(value) == max:
            elected[key] = timestamp[key]
        msg += get_displayname(roomid, key)
        msg += ': '
        msg += str(len(value))
        if value:
            msg += ' ('
            list = ''
            for voter in value:
                list += ', '
                list += get_displayname(roomid, voter)
            msg += list.replace(', ', '', 1)
            msg += ')<br/>'

    my_logger.debug('elected: '+repr(elected))

    msg += '<br/>'

    final = None
    if len(elected) > 1:
        # deadlocked election
        if get_subphase(phase) >= 0x8:
            # auto-resolve
            for key, value in sorted(elected.iteritems(), key=lambda (k,v): (v)):
                final = key
                break
                #msg += key + ' ' + str(value) + '<br/>'
        else:
            # run off
            # USR_DEADLOCKED_E
            dbcursor.execute("""delete from action where roomid=? and action=?""", (roomid, USR_DAY_VOTE))

            phase += 1
            dbcursor.execute("""update room set phase=? where roomid=?""", (phase, roomid))

            my_logger.debug('run-off voting, phase: '+hex(phase))
            # assign actions to players
            dbcursor.execute("""select * from user where roomid=? and status&?""", (roomid, USR_SURVIVE))
            userlist = dbcursor.fetchall()
            for row in userlist:
                my_logger.debug('issue a USR_DAY_VOTE vote to everyone: '+row[0])
                user_status[row[0]] |= USR_DAY_VOTE
                upd_user_status(row[0])

            msg += get_string('sys_deadlocked')
            sys_msg(msg, roomid, phase)

            # run-off voting
            return False

    elif len(elected):
        final = random.choice(elected.items())[0]

    if final:
        msg += get_string('sys_lynched') % get_displayname(roomid, final)
        kill_player(room, final, lynch=True)
        sys_msg(msg, roomid, phase)
        report = get_string('report_lynched') % (get_day_count(phase), get_displayname(roomid, final) )
        report_msg(report, roomid, phase)
    else:
        # no one is hanged
        pass

    # day ended
    return True

def check_vote_night(room, action):
    roomid = room[1]
    options = room[4]
    phase = room[5]

    dbcursor.execute("""select * from action where roomid=? and action=?""", \
        (roomid, action))

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

    final = ''
    if len(elected) > 1:
        for key, value in sorted(elected.iteritems(), key=lambda (k,v): (v)):
            final = key
            break
    elif len(elected) == 1:
        final = random.choice(elected.items())[0]

    if phase>>4 == 1:
        # night zero
        return None

    return final

def check_vote(room):
    global user_status

    roomid = room[1]
    options = room[4]
    phase = room[5]

    dbcursor.execute("""select count(*) from user where roomid=? and status&?""", \
        (roomid, USR_ACT_MASK))
    sqlcount = dbcursor.fetchall()
    user_count = sqlcount[0][0]
    if user_count == -1:
        user_count = 0
    if user_count == 0:
        # all actions are taken
        deadlist = []
        daynight = get_day_night(phase)
        if daynight == 0: # day
            dayend = check_vote_day(room)
            if not dayend:
                return
        elif daynight == 1: # night
            killed = check_vote_night(room, USR_NIGHT_VOTE)
            if killed:
                deadlist.append(killed)
            # handle night actions

        elif phase == 1: # ready check
            game_start(room)

        if not daynight == -1:
            # phase ended
            # process action result
            # advance phase (assign actions)
            my_logger.debug('deadlist: '+repr(deadlist))

            # blocking must be handled before all actions
            dbcursor.execute("""select * from action where roomid=? and action=?""", \
                (roomid, USR_NIGHT_BLOCK))
            userlist = dbcursor.fetchall()
            for user in userlist:
                target = user[3]
                msg = get_string('role_block') % get_displayname(roomid, target)
                private_msg(user[2], msg, roomid, phase)
                dbcursor.execute("""delete from action where roomid=? and username=?""", \
                    (roomid, target))
                my_logger.debug('blocked: '+target)

            # protector check must be placed after night vote counting
            # and before all other night death check
            # so it only protects victims of common night wolf attack
            dbcursor.execute("""select * from action where roomid=? and action=?""", \
                (roomid, USR_NIGHT_HEAL))
            userlist = dbcursor.fetchall()
            for user in userlist:
                target = user[3]
                msg = get_string('role_heal') % get_displayname(roomid, target)
                private_msg(user[2], msg, roomid, phase)
                if target in deadlist:
                    deadlist.remove(target)
                    my_logger.debug('healed: '+target)

            # seer handling
            dbcursor.execute("""select * from action where roomid=? and action=?""", \
                (roomid, USR_NIGHT_SEER))
            userlist = dbcursor.fetchall()
            seerindex = 0
            for user in userlist:
                dbcursor.execute("""select * from user where roomid=? and username=?""", \
                    (roomid, user[3]))
                target = dbcursor.fetchone()
                if target:
                    t_name = target[0]
                    t_role = target[5]
                    t_display = target[9]
                    t_alignment = t_role & PVG_ALIGNMENT_MASK
                    result = get_string('role_villager')
                    if t_alignment:
                        result = get_string('role_wolf')
                    msg = get_string('role_seer') % (t_display, result)
                    private_msg(user[2], msg, roomid, phase)
                    user_status[t_name] |= (USR_TARGET1 + seerindex)
                    seerindex += 1

            # change phase
            phase = phase_advance(room)
            upd_room_ingame(roomid)

            my_logger.debug('deadlist: '+repr(deadlist))

            for killed in deadlist:
                my_logger.debug('killed: '+killed)
                msg = get_string('sys_killed') % get_displayname(roomid, killed)
                kill_player(room, killed)
                sys_msg(msg, roomid, phase)
                report = get_string('report_killed') % (get_day_count(phase), get_displayname(roomid, killed) )
                report_msg(report, roomid, phase)

            if check_game_end(room):
                phase = PHS_AFTERMATH
                dbcursor.execute("""update room set phase=? where roomid=?""", (phase, roomid))
                upd_room_ingame(roomid)

            dbcursor.execute("""select * from user where roomid=?""", (roomid, ))
            userlist = dbcursor.fetchall()
            for user in userlist:
                upd_user_status(user[0])

        # delete all actions before next round
        # as they are all handled
        dbcursor.execute("""delete from action where roomid=?""", (roomid, ))

    else:
        dbcursor.execute("""select username from user where roomid=? and status&? and status&?""", \
            (roomid, USR_CONN, USR_ACT_MASK))
        my_logger.debug('not voted yet: '+str(user_count)+', list: '+repr(dbcursor.fetchall()))

def copy_ruleset(ruleset, roomid):
    global do_later_mask
    dbcursor.execute("""delete from ruleset where id=?""", (roomid, ))
    dbcursor.execute("""select * from ruleset where id=?""", (ruleset,))
    rec = dbcursor.fetchone()
    if rec:
        dbcursor.execute('insert into ruleset values (?,?,?,?,?,?,?,?,?)', \
            (rec[0], roomid, rec[2], ruleset, rec[4], rec[5], rec[6], rec[7], rec[8]))
        do_later_mask |= DLTR_COMMIT_DB
        
def game_start(room):
    global user_status, user_role

    username = room[0]
    roomid = room[1]
    description = room[2]
    ruleset = room[3]
    options = room[4]
    phase = room[5]
    timeout = room[6]
    message = room[7]

    copy_ruleset(ruleset, roomid)
    dbcursor.execute("""select * from ruleset where id=?""", (roomid,))
    ruleset = dbcursor.fetchone()
    if ruleset:
        options = ruleset[2]
        roles = json.loads(ruleset[4])
        nightzero = ruleset[5]
        day = ruleset[6]
        night = ruleset[7]
        runoff = ruleset[8]

        # get best matched role sets
        dbcursor.execute("""select count(*) from user where roomid=?""", (roomid, ))
        sqlcount = dbcursor.fetchall()
        user_count = sqlcount[0][0]
        rset_choice = []
        rset_min = []
        rset_max = []
        rset_final = []
        for rset in sorted(roles, key=lambda (s): (len(s))):
            rset_max = rset
            if not rset_min:
                rset_min = rset
            if len(rset) == user_count:
                rset_choice.append(rset)
        if rset_choice:
            rset_final = random.choice(rset_choice)
        else:
            if user_count < len(rset_min):
                rset_final = rset_min
            else:
                rset_final = rset_max

        my_logger.debug('roleset, participant: '+str(user_count)+', set: '+repr(rset_final))

        # assign role to players
        assign_role = dict
        random.shuffle(rset_final)
        dbcursor.execute("""select * from user where roomid=?""", (roomid, ))
        userlist = dbcursor.fetchall()
        for user in userlist:
            role = rset_final.pop()
            user_role[user[0]] = role
            user_status[user[0]] &= 0xf
            user_status[user[0]] |= USR_SURVIVE
            my_logger.debug('assign role, , user: '+user[0]+', role: '+hex(role))
            dbcursor.execute("""update user set status=?, role=?
                where username=?""", (user_status[user[0]], user_role[user[0]], user[0]))

        # change phase
        phase = phase_advance(room)
        upd_room_ingame(roomid)

        # update user status message and notify user to reload
        for user in userlist:
            upd_user_status(user[0])
            msg_onetime(roomid, user[0], MSG_RELOAD, '')

        my_logger.debug('game_start, room: '+roomid)
    else:
        my_logger.debug('game_start failed, roomid: '+roomid)

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
    if ((phase >> 4) == 0) or (phase > 0xffff):
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

def get_day_count(phase):
    if ((phase >> 4) == 0) or (phase > 0xffff):
        return -1
    return (phase >> 4)/2

def phase_advance(room):
    roomid = room[1]
    description = room[2]
    ruleset = room[3]
    options = room[4]
    phase = room[5]
    timeout = room[6]

    gamestart = False
    if phase < 0x10: # start
        gamestart = True

    phase = ((phase >> 4) + 0x1) << 4
    phase += 0x6 # only apply if there's no pre-election sub-phases
    dbcursor.execute("""update room set phase=? where roomid=?""", (phase, roomid))

    if gamestart:
        #sys_msg('Game started.', roomid, phase)
        pass

    my_logger.debug('phase advanced: '+hex(phase))
    # assign actions to players
    daynight = get_day_night(phase)
    if daynight == 0: # day
        sys_msg(get_string('sys_sunrise') % get_day_count(phase), roomid, phase)

        dbcursor.execute("""select * from user where roomid=? and status&?""", (roomid, USR_SURVIVE))
        userlist = dbcursor.fetchall()
        for row in userlist:
            my_logger.debug('issue a USR_DAY_VOTE vote to everyone: '+row[0])
            user_status[row[0]] &= ~USR_NIGHT_ACT_MASK
            user_status[row[0]] |= USR_DAY_VOTE
            upd_user_status(row[0])

    elif daynight == 1: # night
        sys_msg(get_string('sys_nightfall'), roomid, phase)

        if phase > 0x20: # check this only if "night zero no kill" rule is applied
            dbcursor.execute("""select * from user where roomid=? and status&? and role&?""", (roomid, USR_SURVIVE, ROLE_BITE_MASK))
            userlist = dbcursor.fetchall()
            for row in userlist:
                my_logger.debug('issue a USR_NIGHT_VOTE vote to wolf: '+row[0])
                user_status[row[0]] |= USR_NIGHT_VOTE
                upd_user_status(row[0])
        else:
            #Night zero, RLE_NIGHTZERO
            sys_msg(get_string('sys_nightzero'), roomid, phase)

        if phase > 0x20: # check this only if "night zero no action" rule is applied
            dbcursor.execute("""select * from user where roomid=? and status&? and role&?""", (roomid, USR_SURVIVE, ROLE_BLOCKER))
            userlist = dbcursor.fetchall()
            for row in userlist:
                my_logger.debug('issue a USR_NIGHT_BLOCK vote to blocker: '+row[0])
                user_status[row[0]] |= USR_NIGHT_BLOCK
                upd_user_status(row[0])

            dbcursor.execute("""select * from user where roomid=? and status&? and role&?""", (roomid, USR_SURVIVE, ROLE_SEER))
            userlist = dbcursor.fetchall()
            for row in userlist:
                my_logger.debug('issue a USR_NIGHT_SEER vote to blocker: '+row[0])
                user_status[row[0]] |= USR_NIGHT_SEER
                upd_user_status(row[0])

            dbcursor.execute("""select * from user where roomid=? and status&? and role&?""", (roomid, USR_SURVIVE, ROLE_HEALER))
            userlist = dbcursor.fetchall()
            for row in userlist:
                my_logger.debug('issue a USR_NIGHT_HEAL vote to blocker: '+row[0])
                user_status[row[0]] |= USR_NIGHT_HEAL
                upd_user_status(row[0])

    elif phase > 0xffff: # end
        sys_msg('Game ended.', roomid, phase)

    # set timeout
    dbcursor.execute("""select * from ruleset where id=?""", (roomid,))
    ruleset = dbcursor.fetchone()

    options = ruleset[2]
    nightzero = ruleset[5]
    day = ruleset[6]
    night = ruleset[7]
    runoff = ruleset[8]

    now = get_time_norm()
    timeout = now
    if daynight == 0:
        if get_subphase(phase) == 0x6:
            timeout += day
        else:
            timeout += runoff
    elif daynight == 1:
        if phase < 0x20:
            timeout += nightzero
        else:
            timeout += night
    else:
        timeout = TIME_MAX
    dbcursor.execute("""update room set timeout=? where roomid=?""", \
        (timeout, roomid))
    my_logger.debug('ruleset, day: %d, night: %d, nightzero: %d, runoff: %d' % (day,night,nightzero,runoff))
    my_logger.debug('set timeout, roomid: %s, timeout: %d, left: %d, phase: %s' % (roomid,timeout,timeout-now,hex(phase)))

    return phase

def get_ip_integer(ipstr):
    ipsplit = ipstr.split('.')
    return (int(ipsplit[0]) << 24) + (int(ipsplit[1]) << 16) + (int(ipsplit[2]) << 8) + int(ipsplit[3])
    
def scan_ip_conflict():
    dbcursor.execute("""select * from user where status&?""", (USR_CONN,) )
    userlist = dbcursor.fetchall()
    for user in userlist: 
        if user[0] in user_status:
            check_ip_conflict(user)
    
def check_ip_conflict_username(username):
    dbcursor.execute("""select * from user where username=?""", (username,))
    user = dbcursor.fetchone()
    check_ip_conflict(user)
    
def check_ip_conflict(user):
    global user_status
    ip = user[3]
    roomid = user[4]
    displayname = user[9]
    email = user[10]
    hashname = user[11]
    
    oldstatus = user_status[user[0]] & USR_IPCONFLICT
    user_status[user[0]] &= ~USR_IPCONFLICT
    
    dbcursor.execute("""select * from user where roomid=? and ip&?=? and email!=?""", (roomid, 0xffffff00, ip&0xffffff00, email) )
    conflict = dbcursor.fetchone()
    if conflict:
        print 'conflict0'
        # subnet match
        user_status[user[0]] |= USR_IPCONFLICT
        my_logger.debug('ip partial conflict, ip: '+hex(ip&0xffffff00)+', email: '+email)

    dbcursor.execute("""select * from user where roomid=? and ip=? and email!=?""", (roomid, ip, email) )
    conflict = dbcursor.fetchone()
    if conflict:
        print 'conflict1'
        # exact match
        user_status[user[0]] |= USR_IPCONFLICT
        my_logger.debug('ip conflict, ip: '+hex(ip)+', email: '+email)
        
    if (user_status[user[0]]&USR_IPCONFLICT) != oldstatus:
        upd_user_status(user[0])

def get_timeout_msg(roomid):
    dbcursor.execute("""select * from room where roomid=?""", (roomid,))
    room = dbcursor.fetchone()
    row_serial = None
    if room:
        description = room[2]
        ruleset = room[3]
        options = room[4]
        phase = room[5]
        timeout = room[6]

        timestamp = get_time_norm()
        author = SYSTEM_USER
        message = timeout - timestamp
        type = MSG_TIMEOUT_MSG
        row_serial = (type, author, '', message, timestamp, phase)

    return row_serial

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
            user_activity, user_status, user_role

        if self.path != '/check_update':
            my_logger.debug('post, command: '+self.path+', ip: '+self.client_address[0]+', value: '+self.rfile.getvalue())

        if self.path == '/login':
            #login = unicode(self.rfile.getvalue(), 'utf-8')
            login = self.rfile.getvalue()
            login = login.splitlines()
            print 'login: ', login
            email = u''
            username = u''
            password = u''
            if login[0]:
                email = login[0]
            if login[1]:
                password = login[1]
            print u'email: ', email
            print u'password: ', password

            sessionkey = None
            ip = get_ip_integer(self.client_address[0])

            dbcursor.execute("""select * from user where email=?""", (email,))
            auth = dbcursor.fetchone()
            if auth:
                print 'user exists'
                print auth
                if auth[1] == password:
                    print 'user login'
                    sessionkey = str(uuid.uuid4())
                    roomid = auth[4]
                    dbcursor.execute("""select * from room where roomid=?""", (roomid,) )
                    room = dbcursor.fetchone()
                    if room:
                        # to-do: user in room should stay in room
                        # so user without cookie can back in game if he's disconnected
                        dbcursor.execute("""update user set sessionkey=?, ip=? where email=?""", (sessionkey, ip, email) )
                    else:
                        dbcursor.execute("""update user set sessionkey=?, ip=?, roomid=? where email=?""", (sessionkey, ip, '', email) )
                else:
                    print 'incorrect password'
            else:
                print 'user register'
                sessionkey = str(uuid.uuid4())
                username = str(uuid.uuid4())
                roomid = ''
                role = 0
                status = 0
                privilege = 0
                email_split = email.split('@')
                displayname = email_split[0]
                email = email
                nickname = displayname
                mark = 0
                hashname = hashlib.sha1(email).hexdigest()
                lastactivity = get_time_norm()
                dbcursor.execute('insert into user values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', \
                    (username, password, sessionkey, ip, roomid, \
                    role, status, privilege, lastactivity, displayname, email, hashname, mark, nickname, 0, ''))

            print 'sessionkey: ', sessionkey

            if sessionkey:
                dbcursor.execute("""select * from user where sessionkey=?""", (sessionkey,))
                user = dbcursor.fetchone()
                # check_ip_conflict(user)
                
                self.send_response(200)
                #self.send_header(u'Connection', u'Keep-Alive') #Google Chrome error: Refused to set unsafe header "Connection"
                self.send_header(u'Content-type', u'text/plain')
                self.end_headers()
                ret = json.dumps((sessionkey,username))
                self.outgoing.append(ret)
            else:
                self.send_response(401)
                self.end_headers()
                
        elif self.path == '/dcontent':
            params = self.rfile.getvalue()
            path = 'html' + params

            auth = None
            room = None
            if 'Authorization' in self.headers:
                sessionkey = self.headers['Authorization']
                ip = get_ip_integer(self.client_address[0])
                dbcursor.execute("""select * from user where
                    sessionkey=? and ip=?""", (sessionkey, ip))
                auth = dbcursor.fetchone()

            if auth:
                username = auth[0]
                roomid = auth[4]
                displayname = auth[9]
                email = auth[10]
                mark = auth[12]
                nickname = auth[13]

                with open(path) as hfile:
                    dcontent = unicode(hfile.read(), 'utf-8')
                    self.send_response(200)
                    #self.send_header(u'Connection', u'Keep-Alive') #Google Chrome error: Refused to set unsafe header "Connection"
                    self.send_header(u'Content-type', u'text/plain')
                    self.end_headers()
                    subst = None
                    if params == "/host.html":
                        dbcursor.execute("""select * from ruleset where baseset=?""", ('',))
                        subst = u''
                        reclist = dbcursor.fetchall()
                        for rec in reclist:
                            subst += u'<option value="%s">%s</option>' % (rec[1], rec[0])
                    elif params == "/profile.html":
                        subst = (email, nickname)
                    if subst:
                        dcontent = dcontent % subst
                    self.outgoing.append(dcontent.encode('utf-8'))

            else:
                self.send_response(200)
                self.end_headers()

        elif self.path == '/check_credential':
            email = self.rfile.getvalue()
            ip = get_ip_integer(self.client_address[0])
            dbcursor.execute("""select * from user where email=?""", (email,) )
            user = dbcursor.fetchone()
            if user:
                self.send_response(202)
                self.end_headers()
            else:
                self.send_response(200)
                self.end_headers()
        
        elif self.path == '/profile':
            auth = None
            room = None
            if 'Authorization' in self.headers:
                sessionkey = self.headers['Authorization']
                ip = get_ip_integer(self.client_address[0])
                dbcursor.execute("""select * from user where
                    sessionkey=? and ip=?""", (sessionkey, ip))
                auth = dbcursor.fetchone()

            if auth:
                nickname = unicode(self.headers['From'], 'utf-8')
                username = auth[0]
                roomid = auth[4]
                displayname = html_escape(nickname)
                email = auth[10]
                mark = auth[12]
                dbcursor.execute("""update user set nickname=?, displayname=? where sessionkey=?""", (nickname, displayname, sessionkey))
                upd_user_status(username);

                self.send_response(205)
                self.end_headers()
            
        elif self.path == '/logout':
            sessionkey = self.rfile.getvalue()
            ip = get_ip_integer(self.client_address[0])
            dbcursor.execute("""select * from user where sessionkey=? and ip=?""", (sessionkey,ip))
            auth = dbcursor.fetchone()
            if auth:
                username = auth[0]
                hashname = auth[11]
                user_status.pop(username)
                reset = str(uuid.uuid4())
                dbcursor.execute("""update user set sessionkey=?, ip=?, roomid=? where sessionkey=?""", (reset, 0, '', sessionkey))
                dbcursor.execute("""delete from message where username=? and (type=? or type=? or type=?)""", \
                    (username, MSG_USER_STATUS, MSG_USR_STA_PRIVATE, MSG_USR_STA_ALIGNMENT))
                #do_later_mask |= DLTR_COMMIT_DB
                conn.commit()
                msg_command(auth[4], MSG_USERQUIT, hashname)

            self.send_response(205)
            self.end_headers()

        elif self.path == '/drop':
            auth = None
            room = None
            if 'Authorization' in self.headers:
                sessionkey = self.headers['Authorization']
                ip = get_ip_integer(self.client_address[0])
                dbcursor.execute("""select * from user where
                    sessionkey=? and ip=?""", (sessionkey, ip))
                auth = dbcursor.fetchone()

            if auth:
                username = auth[0]
                roomid = auth[4]
                status = user_status[username]

                dbcursor.execute("""select * from room where roomid=?""", \
                    (roomid, ))
                room = dbcursor.fetchone()

                if room:
                    my_logger.debug('/drop, room: '+roomid+', host: '+room[0]+', username: '+username)
                    if room[0] == username:
                        dbcursor.execute("""delete from message where username=? and type=?""", (roomid, MSG_ROOM))
                        dbcursor.execute("""delete from room where roomid=?""", (roomid, ))

                        msg_command(roomid, MSG_GAMEDROP_P, roomid)
                        msg_command('', MSG_GAMEDROP, roomid)

                dbcursor.execute("""update user set roomid=?, privilege=? where username=?""", \
                    ('', 0, username))
                #check_ip_conflict_username(username)
                scan_ip_conflict()
                #user_status[username] &= ~USR_HOST
                upd_user_status(username)

                do_later_mask |= DLTR_COMMIT_DB

                self.send_response(205)
                self.end_headers()

        elif self.path == '/ready':
            auth = None
            room = None
            if 'Authorization' in self.headers:
                sessionkey = self.headers['Authorization']
                ip = get_ip_integer(self.client_address[0])
                dbcursor.execute("""select * from user where
                    sessionkey=? and ip=?""", (sessionkey, ip))
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
                        to_upd = []
                        if room[5] == 0:
                            """Enter phase 1(ready check). The match starts after everyone votes for someone.
                            This is to make sure everyone knows how the game proceeds.
                            """
                            dbcursor.execute("""update room set phase=1 where roomid=?""", (roomid, ))
                            dbcursor.execute("""delete from action where roomid=?""", (roomid, ))
                            for row in userlist:
                                my_logger.debug('issue a USR_DAY_VOTE vote to user: '+row[0])
                                user_status[row[0]] |= USR_DAY_VOTE
                                upd_user_status(row[0])

                            sys_msg(get_string('sys_voteready'), roomid)
                        else:
                            dbcursor.execute("""update room set phase=0 where roomid=?""", (roomid, ))
                            dbcursor.execute("""delete from action where roomid=?""", (roomid, ))
                            for row in userlist:
                                my_logger.debug('remove USR_DAY_VOTE vote from user: '+row[0])
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
                ip = get_ip_integer(self.client_address[0])
                dbcursor.execute("""select * from user where
                    sessionkey=? and ip=?""", (sessionkey, ip))
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
                            check_vote(room)

                self.send_response(204)
                self.end_headers()

        elif self.path == '/target':
            auth = None
            action = 0
            if 'Authorization' in self.headers:
                sessionkey = self.headers['Authorization']
                ip = get_ip_integer(self.client_address[0])
                dbcursor.execute("""select * from user where
                    sessionkey=? and ip=?""", (sessionkey, ip))
                auth = dbcursor.fetchone()
            if 'From' in self.headers: # From is used as Action, sincs custom header X-Action does not work in IE
                action = int(self.headers['From'])

            if auth:
                username = auth[0]
                roomid = auth[4]

                dbcursor.execute("""select * from room where roomid=?""", \
                    (roomid, ))
                room = dbcursor.fetchone()

                if room:
                    if user_status[username] & action:
                        targetname = self.rfile.getvalue().decode('utf-8')
                        dbcursor.execute("""select * from user where roomid=? and username=?""", (roomid, targetname, ))
                        target = dbcursor.fetchone()

                        my_logger.debug('/target, username: '+username+', targetname: '+targetname+', action: '+hex(action))

                        if target:
                            #sys_msg(username+' voted for '+targetname, roomid)
                            user_status[username] &= ~action
                            upd_user_status(username)

                            dbcursor.execute('insert into action values (?,?,?,?,?)', \
                                (roomid, action, username, targetname, get_time_norm()))
                            check_vote(room)

                self.send_response(204)
                self.end_headers()

        elif self.path == '/kick':
            auth = None
            if 'Authorization' in self.headers:
                sessionkey = self.headers['Authorization']
                ip = get_ip_integer(self.client_address[0])
                dbcursor.execute("""select * from user where
                    sessionkey=? and ip=?""", (sessionkey, ip))
                auth = dbcursor.fetchone()

            if auth:
                username = auth[0]
                roomid = auth[4]
                if user_status[username] & USR_HOST:
                    targetname = self.rfile.getvalue().decode('utf-8')
                    print 'targetname: ', targetname
                    print 'roomid: ', roomid
                    dbcursor.execute("""select * from user where
                        username=? and roomid=?""", (targetname, roomid))
                    target = dbcursor.fetchone()
                    if target:
                        print 'check3'
                        targethash = target[11]
                        dbcursor.execute("""update user set roomid=?, privilege=? where username=?""", \
                            ('', 0, targetname))
                        user_status[targetname] |= USR_KICKED
                        #check_ip_conflict_username(username)
                        scan_ip_conflict()
                        upd_user_status(targetname)
                        upd_room(roomid)

                        msg_command(roomid, MSG_USERQUIT, targethash)

                        do_later_mask |= DLTR_COMMIT_DB

                        my_logger.debug('/kick/, username: '+targetname+', roomid: '+roomid)

                self.send_response(204)
                self.end_headers()

        elif self.path == '/drop_confirm':
            auth = None
            if 'Authorization' in self.headers:
                sessionkey = self.headers['Authorization']
                ip = get_ip_integer(self.client_address[0])
                dbcursor.execute("""select * from user where
                    sessionkey=? and ip=?""", (sessionkey, ip))
                auth = dbcursor.fetchone()

            if auth:
                username = auth[0]
                user_status[username] &= ~USR_KICKED
                upd_user_status(username)
                do_later_mask |= DLTR_COMMIT_DB

                self.send_response(205)
                self.end_headers()
            else:
                self.send_response(401)
                self.end_headers()

        elif self.path == '/quit':
            auth = None
            if 'Authorization' in self.headers:
                sessionkey = self.headers['Authorization']
                ip = get_ip_integer(self.client_address[0])
                dbcursor.execute("""select * from user where
                    sessionkey=? and ip=?""", (sessionkey, ip))
                auth = dbcursor.fetchone()

            if auth:
                msg_command(auth[4], MSG_USERQUIT, auth[11])
                dbcursor.execute("""update user set roomid=?, privilege=? where username=?""", \
                    ('', 0, auth[0]))
                #check_ip_conflict_username(auth[0])
                scan_ip_conflict()
                upd_user_status(auth[0])
                do_later_mask |= DLTR_COMMIT_DB

                my_logger.debug('/quit/, username: '+auth[0]+', roomid: '+auth[4])
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
                ip = get_ip_integer(self.client_address[0])
                dbcursor.execute("""select * from user where
                    sessionkey=? and ip=?""", (sessionkey, ip))
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
                        msg_command(auth[4], MSG_USERQUIT, auth[11])
                        dbcursor.execute("""update user set roomid=? where username=?""", \
                            (roomid, auth[0]))
                        #check_ip_conflict_username(auth[0])
                        scan_ip_conflict()
                        user_status[auth[0]] &= ~USR_ACT_MASK
                        upd_user_status(auth[0])
                        do_later_mask |= DLTR_COMMIT_DB

                        my_logger.debug('/join/, username: '+auth[0]+', roomid: '+roomid)
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
                ip = get_ip_integer(self.client_address[0])
                dbcursor.execute("""select * from user where
                    sessionkey=? and ip=?""", (sessionkey, ip))
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
            phase = 0
            privilege = 0
            username = author
            maskip = str(rndtable256[ip>>24]) + '.' + \
                str(rndtable256[(ip&0xff0000)>>16]) + '.' + \
                str(rndtable256[(ip&0xff00)>>8]) + '.' + \
                str(rndtable256[ip&0xff])
            displayname = maskip
            dosend = True
            ct = time.localtime(now)
            if auth:
                username = auth[0]
                roomid = auth[4]
                role = auth[5]
                user_privilege = auth[7]
                displayname = auth[9]
                email = auth[10]
                alignment = role & PVG_ALIGNMENT_MASK

                # check if user has privilege to speak

                dbcursor.execute("""select * from room where roomid=?""", (roomid, ))
                room = dbcursor.fetchone()

                if room:
                    if auth[6]&USR_SURVIVE:
                        phase = room[5]
                        daynight = get_day_night(phase)
                        if daynight == 0: # day
                            privilege |= PVG_DAYCHAT
                            pass
                        elif daynight == 1: # night
                            if not (user_privilege & PVG_NIGHTCHAT):
                                dosend = False
                            privilege |= alignment
                        else:
                            privilege |= PVG_ROOMCHAT
                    else:
                        privilege |= PVG_ROOMCHAT

            if dosend:
                isoformat = datetime.time(ct.tm_hour,ct.tm_min,ct.tm_sec).isoformat()
                message = msgbody
                dbcursor.execute('insert into message values (?,?,?,?,?,?,?,?,?,?,?,?)', \
                    (roomid, timestamp, privilege, username, isoformat, message, 0, phase, '', displayname, 0, ''))
                do_later_mask |= DLTR_COMMIT_DB

                dbcursor.execute("""update user set lastactivity=? where username=?""", \
                    (timestamp, username))

            self.send_response(204)
            self.end_headers()

        elif self.path == '/check_update':
            auth = None
            if 'Authorization' in self.headers:
                sessionkey = self.headers['Authorization']
                ip = get_ip_integer(self.client_address[0])

                dbcursor.execute("""select * from user where
                    sessionkey=? and ip=?""", (sessionkey, ip))
                auth = dbcursor.fetchone()
                #print auth
                #time.sleep(100)

                if auth:
                    user_activity[auth[0]] = get_time_norm()
                    if auth[0] not in user_status:
                        user_status[auth[0]] = auth[6] & ~USR_CONN
                    if not user_status[auth[0]] & USR_CONN:
                        # user connected
                        user_status[auth[0]] |= USR_CONN
                        #check_ip_conflict(auth)
                        scan_ip_conflict()
                        upd_user_status(auth[0])
                        my_logger.debug('user connected, user: '+auth[0])

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
                where timestamp>? and roomid=? and ((privilege&?=privilege) or (type&? and receiver=?))""", \
                (client_doc_time, roomid, privilege, MSG_PRIVATE_MASK, username))
            msglist = dbcursor.fetchall()
            json_serial = []
            for row in msglist:
                #print row
                timestamp = row[1]
                author = row[3]
                isoformat = row[4]
                message = row[5]
                type = row[6]
                phase = row[7]
                displayname = row[9]
                row_serial = (type, displayname, isoformat, message, timestamp, phase)
                json_serial.append(row_serial)

            dbcursor.execute("""delete from message \
                where timestamp>? and roomid=? and (type&? and receiver=?)""", \
                (client_doc_time, roomid, MSG_ONETIME_MASK, username))

            if json_serial:
                if roomid:
                    tmsg = get_timeout_msg(roomid)
                    if tmsg:
                        json_serial.append(tmsg)

                ret = json.dumps(json_serial)

                #my_logger.debug('/check_update, username: '+username+', content: '+ret)

                self.send_response(200)
                #self.send_header(u'Connection', u'Keep-Alive') #Google Chrome error: Refused to set unsafe header "Connection"
                self.send_header(u'Content-type', u'text/plain')
                self.end_headers()
                self.outgoing.append(ret)
            elif auth:
                self.send_response(204)
                #self.send_header(u'Connection', u'Keep-Alive')
                #self.send_header(u'Content-Length', u'0')
                self.end_headers()
            else:
                self.send_response(401)
                #self.send_header(u'Connection', u'Keep-Alive') #Google Chrome error: Refused to set unsafe header "Connection"
                self.send_header(u'Content-Length', u'0')
                self.end_headers()
            check_do_later()

        elif self.path == '/hostex':
            auth = None
            if 'Authorization' in self.headers:
                sessionkey = self.headers['Authorization']
                ip = get_ip_integer(self.client_address[0])
                dbcursor.execute("""select * from user where
                    sessionkey=? and ip=?""", (sessionkey, ip))
                auth = dbcursor.fetchone()

            if auth:
                ruleset = ''
                description = ''
                print 'json: ', self.rfile.getvalue()
                contentjson = json.loads(self.rfile.getvalue() )
                ruleset = contentjson[0]
                description = contentjson[1]
                message = html_escape(contentjson[2])
                """if 'Pragma' in self.headers: #Header 'Pragma' is modified by Firefox
                    ruleset = self.headers['Pragma']
                if 'From' in self.headers:
                    description = unicode(self.headers['From'], 'utf-8')
                    description = html_escape(description)"""

                roomid = str(uuid.uuid4())
                username = auth[0]
                displayname = auth[9]
                email = auth[10]
                hashname = auth[11]
                if not description:
                    description = get_string('rnd_gamename')
                    description = description.replace('\n', '')
                if not description:
                    description = roomid
                description = html_escape(description)
                options = 0
                phase = 0
                timeout = TIME_MAX
                dbcursor.execute('insert into room values (?,?,?,?,?,?,?,?,?,?)', \
                    (username, roomid, description, ruleset, options, phase, timeout, message, 0, ''))
                dbcursor.execute("""update user set roomid=? where username=?""", \
                    (roomid, username))

                timestamp = get_time_norm()
                privilege = 0
                participant = 1
                host = displayname
                if not host:
                    host = email
                if not host:
                    host = username
                json_serial = (description, ruleset, options, phase, host, roomid, participant, message)
                message = json.dumps(json_serial)
                dbcursor.execute('insert into message values (?,?,?,?,?,?,?,?,?,?,?,?)', \
                    ('', timestamp, 0, roomid, '', message, MSG_ROOM, 0, '', '[dsp]', 0, ''))

                sys_msg(get_string('sys_welcome') % description, roomid)
                my_logger.debug('/hostex, room: '+roomid+', host: '+username)
                #user_status[username] |= USR_HOST

                upd_room(roomid)
                #check_ip_conflict_username(auth[0])
                scan_ip_conflict()
                user_status[username] &= ~USR_ACT_MASK
                upd_user_status(username)
                do_later_mask |= DLTR_COMMIT_DB
                msg_command('', MSG_USERQUIT, hashname)

                self.send_response(205)
                self.end_headers()
            else:
                self.send_response(401)
                self.end_headers()

        elif self.path == '/get_ruleset':
            dbcursor.execute("""select * from ruleset where baseset=?""", ('',))
            ret = u''
            for rec in dbcursor:
                ret += u'<option value="%s">%s</option>' % (rec[1], rec[0])

            if ret:
                self.send_response(200)
                #self.send_header(u'Connection', u'Keep-Alive') #Google Chrome error: Refused to set unsafe header "Connection"
                self.send_header(u'Content-type', u'text/plain')
                self.end_headers()
                self.outgoing.append(ret)
            else:
                self.send_response(204)
                #self.send_header(u'Connection', u'Keep-Alive') #Google Chrome error: Refused to set unsafe header "Connection"
                self.send_header(u'Content-Length', u'0')
                self.end_headers()

        # signal the end of this request
        self.outgoing.append(None)

    def handle_data(self):
        if self.command == 'GET':
            self.handle_get()
        elif self.command == 'POST':
            self.handle_post()

if __name__=="__main__":
    # init other modules
    # init other modules
    random.seed()

    for i in range(256):
        rndtable256.append(i)
    random.shuffle(rndtable256)

    # launch the server on the specified port
    now = get_time_norm()
    do_later_short = now + INTERVAL_SHORT
    do_later_long = now + INTERVAL_LONG

    # clear temp states
    dbcursor.execute("""delete from message where roomid='' and (type=? or type=? or type=?)""", \
        (MSG_USER_STATUS, MSG_USR_STA_PRIVATE, MSG_USR_STA_ALIGNMENT) )
    dbcursor.execute("""delete from message where (type=? or type=? or type=?)""", \
        (MSG_USERQUIT, MSG_GAMEDROP, MSG_GAMEDROP_P) )
    dbcursor.execute("""select * from user where status&?""", (USR_CONN, ))
    userlist = dbcursor.fetchall()
    for user in userlist:
        user_status[user[0]] = user[6]
    for user in userlist: # 2 steps to avoid KeyError when accesing user_status[username]
        #check_ip_conflict(user)
        scan_ip_conflict()
        upd_user_status(user[0])

    dbcursor.execute("""select * from room""")
    roomlist = dbcursor.fetchall()
    for room in roomlist:
        roomid = room[1]
        description = room[2]
        ruleset = room[3]
        options = room[4]
        phase = room[5]
        timeout = room[6]
        message = room[7]

        dbcursor.execute("""select count(*) from user where roomid=?""", (roomid, ))
        sqlcount = dbcursor.fetchall()
        user_count = sqlcount[0][0]
        if user_count > 0:
            if phase >= 0x10:
                upd_room_ingame(roomid)
            else:
                upd_room(roomid)

    port = HTTP_PORT
    s = Server('', port, MyHandler)
    print "SimpleAsyncHTTPServer running on port %s" % port
    try:
        asyncore.loop()
    except KeyboardInterrupt:
        conn.commit()
        conn.close()
        print "Crtl+C pressed. Shutting down."