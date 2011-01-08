d = dict()
a = ('b', 'd')
b = ('a')
c = ('a', 'b', 'd', 'k')
d['a'] = a
d['b'] = b
d['c'] = c

for key, value in sorted(d.iteritems(), key=lambda (k,v): (len(v)), reverse=True):
    print key, ': ', value


s = set()
s.add(123)
print s