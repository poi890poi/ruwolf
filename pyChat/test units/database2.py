import sqlite3
import os
import sys

appdata = os.path.join(os.environ['APPDATA'], u'MyPythonApp')
if not os.path.isdir(appdata):
    os.mkdir(appdata)
dbf = os.path.join(appdata, u'pychat.db')

conn = sqlite3.connect(dbf)

dbconn = conn.cursor()

username = u'admin'
dbconn.execute('select * from user where username=?', (username,))
#dbconn.execute('select * from user where username="%s"' % username)
print dbconn.fetchone()
if dbconn.rowcount == 1:
    print 'username exist'
else:
    print 'username not exist'

# We can also close the cursor if we are done with it
dbconn.close()