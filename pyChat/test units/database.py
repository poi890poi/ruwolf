import sqlite3
import os
import sys

INIT_DIR = u'f:\\music2'
for entry in os.listdir(INIT_DIR):
    print type(entry)
    print entry

appdata = os.path.join(os.environ['APPDATA'], u'MyPythonApp')
if not os.path.isdir(appdata):
    os.mkdir(appdata)
dbf = os.path.join(appdata, u'dbx')

conn = sqlite3.connect(dbf)

c = conn.cursor()

# Create table
c.execute('''create table if not exists stocks 
(date text, trans text, symbol text,
 qty real, price real)''')

# Insert a row of data
c.execute("""insert into stocks
          values ('2006-01-05','BUY','RHAT',100,35.14)""")
          
# Save (commit) the changes
conn.commit()

c.execute('select * from stocks')
for row in c:
    print row

# We can also close the cursor if we are done with it
c.close()