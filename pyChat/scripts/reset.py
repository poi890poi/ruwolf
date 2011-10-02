import os
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
dbcursor.execute('''drop table message''')
dbcursor.execute('''drop table delaymsg''')
dbcursor.execute('''drop table user''')
dbcursor.execute('''drop table room''')
dbcursor.execute('''drop table action''')
dbcursor.execute('''drop table ruleset''')

print '''Database reset done.
Run setup.py to initialize database.'''
