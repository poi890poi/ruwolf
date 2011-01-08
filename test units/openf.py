import random

with open('gamename.txt') as hfile:
    l = hfile.readlines()
    print l
    print type(l)
    print random.choice(l).decode('utf-8')
    #description = random.choice()
