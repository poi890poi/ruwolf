import os
import json
import sqlite3

from constant import *

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
datetime text, message text, type integer, phase integer, reserved1 integer, reserved2 text)''')

dbcursor.execute('''create table if not exists user
(username text, password text, sessionkey text, ip text, roomid text,
role integer, status integer, privilege integer, lastactivity integer,
registername text, email text, hashname text, reserved1 integer, reserved2 text)''')

dbcursor.execute('''create table if not exists room
(username text, roomid text, description text, ruleset text, options integer,
phase integer, timeout integer, message text, reserved1 integer, reserved2 text)''')

dbcursor.execute('''create table if not exists action
(roomid text, action integer, username text, target text, timestamp integer)''')

dbcursor.execute('''drop table ruleset''')

dbcursor.execute('''create table if not exists ruleset
(description text, id text, options integer, baseset text, roles text,
nightzero integer, day integer, night integer, runoff integer)''')

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
rset.append(wolf)
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
    rset = []
    for i in range(2): rset.append(wolf)
    for i in range(vn): rset.append(ROLE_VILLAGER)
    roles.append(rset)
for vn in range(5, 8):
    rset = []
    for i in range(3): rset.append(wolf)
    for i in range(vn): rset.append(ROLE_VILLAGER)
    roles.append(rset)
for vn in range(7, 10):
    rset = []
    for i in range(4): rset.append(wolf)
    for i in range(vn): rset.append(ROLE_VILLAGER)
    roles.append(rset)
for vn in range(9, 12):
    rset = []
    for i in range(5): rset.append(wolf)
    for i in range(vn): rset.append(ROLE_VILLAGER)
    roles.append(rset)
nightzero = 15 * INTERVAL_SEC
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
    rset = []
    for i in range(2): rset.append(wolf)
    for i in range(1): rset.append(ROLE_SEER)
    for i in range(vn): rset.append(ROLE_VILLAGER)
    roles.append(rset)
for vn in range(13, 22):
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
    rset = []
    for i in range(1): rset.append(wolf)
    for i in range(1): rset.append(blocker)
    for i in range(1): rset.append(ROLE_SEER)
    for i in range(1): rset.append(ROLE_HEALER)
    for i in range(vn): rset.append(ROLE_VILLAGER)
    roles.append(rset)
for vn in range(7, 8):
    rset = []
    for i in range(1): rset.append(wolf)
    for i in range(1): rset.append(blocker)
    for i in range(vn): rset.append(ROLE_VILLAGER)
    roles.append(rset)
for vn in range(6, 7):
    rset = []
    for i in range(2): rset.append(wolf)
    for i in range(1): rset.append(ROLE_SEER)
    for i in range(vn): rset.append(ROLE_VILLAGER)
    roles.append(rset)
for vn in range(5, 6):
    rset = []
    for i in range(2): rset.append(wolf)
    for i in range(1): rset.append(ROLE_HEALER)
    for i in range(vn): rset.append(ROLE_VILLAGER)
    roles.append(rset)

nightzero = 15 * INTERVAL_SEC
day = 6 * INTERVAL_MIN
night = 2 * INTERVAL_MIN
runoff = 30 * INTERVAL_SEC
dbcursor.execute('insert into ruleset values (?,?,?,?,?,?,?,?,?)', \
    (description, id, options, baseset, json.dumps(roles), nightzero, day, night, runoff))

conn.commit()

"""with open('.//html//hosttemp.html') as hfile:
    content = unicode(hfile.read(), 'utf-8')
    items = u''
    dbcursor.execute('select * from ruleset')
    for rec in dbcursor:
        items += u'<option value="%s">%s</option>' % (rec[1], rec[0])
    with open('.//html//host.html', 'w+') as hfilew:
        hfilew.truncate(0)
        hfilew.write((content % items).encode('utf-8'))"""

