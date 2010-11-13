import SimpleHTTPServer
import SocketServer
import time

PORT = 80

svr_doc_time = '%8.2f' % time.clock()

class MyHTTPServer(SimpleHTTPServer.SimpleHTTPRequestHandler):
    def do_GET(self):
        global svr_doc_time
        print 'path ', self.path
        if self.path == '/checkpoint1':
            svr_doc_time = '%8.2f' % time.clock()
            self.send_response(200)
            self.send_header(u'Content-type', u'text/html')
            self.end_headers()
            self.wfile.write(svr_doc_time)
        elif self.path.startswith('/timestamp/'):
            client_doc_time = self.path
            client_doc_time = client_doc_time.replace('/timestamp/', '')
            client_doc_time = client_doc_time.lstrip()
            print 'TIMESTAMP ', client_doc_time
            update = 'false';
            if float(svr_doc_time) < float(client_doc_time):
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
            print template
            self.send_response(200)
            self.send_header(u'Content-type', u'text/html')
            self.end_headers()
            self.wfile.write(template)
        return

Handler = MyHTTPServer

httpd = SocketServer.TCPServer(("", PORT), Handler)

print "serving at port", PORT
httpd.serve_forever()