#!/usr/bin/env python

import sys, uuid

def genxid(x, y):
    a = int(str(x),16)
    b = int(str(y),16)
    c = (a ^ b) % 0xffffffffffffffffffffffffffffffff
    xid = uuid.UUID(int=c)
    #print a, b, c, xid
    return xid

if __name__ == "__main__": 
    if len(sys.argv) < 3:
        sys.exit('Usage: scripts/genxid.py path hash-object')
    print genxid(sys.argv[1], sys.argv[2])

