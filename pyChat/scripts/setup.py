import os
import json
import sqlite3

from constant import *

# init database

appdata = os.path.join(os.environ['APPDATA'], APPDATA_FOLDER)
appdata = u'userdata'
if not os.path.isdir(appdata):
    os.mkdir(appdata)
dbf = os.path.join(appdata, DB_FILENAME)
conn = sqlite3.connect(dbf)
dbcursor = conn.cursor()

# Create table
dbcursor.execute('''create table if not exists message
(roomid text, timestamp integer, privilege integer, username text,
datetime text, message text, type integer, phase integer, receiver text, displayname text, reserved1 integer, reserved2 text)''')

dbcursor.execute('''create table if not exists delaymsg
(roomid text, timestamp integer, privilege integer, username text,
datetime text, message text, type integer, phase integer, receiver text, displayname text, reserved1 integer, reserved2 text)''')

dbcursor.execute('''create table if not exists user
(username text, password text, sessionkey text, ip integer, roomid text,
role integer, status integer, privilege integer, lastactivity integer,
displayname text, email text, hashname text, mark integer, nickname text, reserved1 integer, reserved2 text)''')

dbcursor.execute('''create table if not exists room
(username text, roomid text, description text, ruleset text, options integer,
phase integer, timeout integer, message text, reserved1 integer, reserved2 text)''')

dbcursor.execute('''create table if not exists action
(roomid text, action integer, username text, target text, timestamp integer)''')

dbcursor.execute('''drop table ruleset''') # drop ruleset as there's no user data at all in it

dbcursor.execute('''create table if not exists ruleset
(description text, id text, options integer, baseset text, roles text,
nightzero integer, day integer, night integer, runoff integer)''')

# print column index/name
parse_state = 0
index = 0
with open(u'scripts//setup.py') as hfile:
    for line in hfile.readlines():
        if parse_state == 0:
            # initial
            if line.find(u"('''create table if not exists") != -1 and line.find(u'line.find(') == -1:
                parse_state = 1
                index = 0
                print line,
        elif parse_state == 1:
            # get columns
            line = line.replace(u'(', u'')
            for col in line.split(u','):
                if col.strip():
                    print index, col.lstrip()
                    index += 1
            if line.find(u")''')") != -1:
                parse_state = 0
                print   

# print function name
with open(u'scripts//async.py') as hfile:
    for line in hfile.readlines():
        if line.find('def ') != -1:
            print line.lstrip(),

print

# print http commands
with open(u'scripts//async.py') as hfile:
    for line in hfile.readlines():
        if line.find('self.path == ') != -1:
            print line.lstrip(),

print

# init rule sets

wolf = (0x1 << ROLE_ALIGNMENT_SHIFT) | ROLE_WOLF
blocker = (0x1 << ROLE_ALIGNMENT_SHIFT) | ROLE_BLOCKER

description = u'Davidoff original'
id = 'davidoff_classic'
options = RLE_VOTE_RUNOFF | RLE_NIGHTVOTE_AGREE
baseset = ''
roles = []

# for test only
rset = []
rset.append(blocker)
rset.append(ROLE_HEALER)
rset.append(ROLE_SEER)
roles.append(rset)
for vn in range(3, 5):
    # for test only
    rset = []
    for i in range(1): rset.append(wolf)
    for i in range(vn): rset.append(ROLE_VILLAGER)
    roles.append(rset)

for vn in range(4, 6):
    # 2 wolves, 4~5 villagers
    rset = []
    for i in range(2): rset.append(wolf)
    for i in range(vn): rset.append(ROLE_VILLAGER)
    roles.append(rset)
for vn in range(5, 8):
    # 3 wolves, 5~7 villagers
    rset = []
    for i in range(3): rset.append(wolf)
    for i in range(vn): rset.append(ROLE_VILLAGER)
    roles.append(rset)
for vn in range(7, 10):
    # 4 wolves, 7~9 villagers
    rset = []
    for i in range(4): rset.append(wolf)
    for i in range(vn): rset.append(ROLE_VILLAGER)
    roles.append(rset)
for vn in range(9, 12):
    # 5 wolves, 9~11 villagers
    rset = []
    for i in range(5): rset.append(wolf)
    for i in range(vn): rset.append(ROLE_VILLAGER)
    roles.append(rset)
nightzero = 30 * INTERVAL_SEC
day = 6 * INTERVAL_MIN
night = 2 * INTERVAL_MIN
runoff = 30 * INTERVAL_SEC
dbcursor.execute('insert into ruleset values (?,?,?,?,?,?,?,?,?)', \
    (description, id, options, baseset, json.dumps(roles), nightzero, day, night, runoff))

description = u'Zarf classic'
id = 'zarf_classic'
options = RLE_VOTE_RUNOFF | RLE_NIGHTZERO | RLE_NIGHTTALK
baseset = ''
roles = []

# 1 wolf is for test only
for vn in range(1, 5):
    rset = []
    for i in range(1): rset.append(wolf)
    for i in range(1): rset.append(ROLE_SEER)
    for i in range(vn): rset.append(ROLE_VILLAGER)
    roles.append(rset)

for vn in range(4, 14):
    # 2 wolves, 1 seer, 4~13 villagers
    rset = []
    for i in range(2): rset.append(wolf)
    for i in range(1): rset.append(ROLE_SEER)
    for i in range(vn): rset.append(ROLE_VILLAGER)
    roles.append(rset)
for vn in range(13, 22):
    # 3 wolves, 1 seer, 13~21 villagers
    rset = []
    for i in range(3): rset.append(wolf)
    for i in range(1): rset.append(ROLE_SEER)
    for i in range(vn): rset.append(ROLE_VILLAGER)
    roles.append(rset)
nightzero = 15 * INTERVAL_SEC
day = 6 * INTERVAL_MIN
night = 2 * INTERVAL_MIN
runoff = 30 * INTERVAL_SEC
dbcursor.execute('insert into ruleset values (?,?,?,?,?,?,?,?,?)', \
    (description, id, options, baseset, json.dumps(roles), nightzero, day, night, runoff))

description = u'Mafiascum F11'
id = 'mafiascum_f11'
options = RLE_VOTE_RUNOFF | RLE_NIGHTZERO | RLE_NIGHTTALK
baseset = ''
roles = []
for vn in range(5, 6):
    # wolf, blocker, healer, 5 villagers
    rset = []
    for i in range(1): rset.append(wolf)
    for i in range(1): rset.append(blocker)
    for i in range(1): rset.append(ROLE_SEER)
    for i in range(1): rset.append(ROLE_HEALER)
    for i in range(vn): rset.append(ROLE_VILLAGER)
    roles.append(rset)
for vn in range(7, 8):
    # wolf, blocker, 7 villagers
    rset = []
    for i in range(1): rset.append(wolf)
    for i in range(1): rset.append(blocker)
    for i in range(vn): rset.append(ROLE_VILLAGER)
    roles.append(rset)
for vn in range(6, 7):
    # 2 wolves, seer, 6 villagers
    rset = []
    for i in range(2): rset.append(wolf)
    for i in range(1): rset.append(ROLE_SEER)
    for i in range(vn): rset.append(ROLE_VILLAGER)
    roles.append(rset)
for vn in range(5, 6):
    # 2 wolves, healer, 5 villagers
    rset = []
    for i in range(2): rset.append(wolf)
    for i in range(1): rset.append(ROLE_HEALER)
    for i in range(vn): rset.append(ROLE_VILLAGER)
    roles.append(rset)

nightzero = 30 * INTERVAL_SEC
day = 6 * INTERVAL_MIN
night = 2 * INTERVAL_MIN
runoff = 30 * INTERVAL_SEC
dbcursor.execute('insert into ruleset values (?,?,?,?,?,?,?,?,?)', \
    (description, id, options, baseset, json.dumps(roles), nightzero, day, night, runoff))

conn.commit()

print '''Setup done.
Run async.py to start the server.'''

"""with open('.//html//hosttemp.html') as hfile:
    content = unicode(hfile.read(), 'utf-8')
    items = u''
    dbcursor.execute('select * from ruleset')
    for rec in dbcursor:
        items += u'<option value="%s">%s</option>' % (rec[1], rec[0])
    with open('.//html//host.html', 'w+') as hfilew:
        hfilew.truncate(0)
        hfilew.write((content % items).encode('utf-8'))"""

