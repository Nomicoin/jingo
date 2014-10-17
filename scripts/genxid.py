#!/usr/bin/env python

import sys, uuid

def genxid(path, hash):
    a = int("".join([c.encode("hex") for c in path]),16)
    b = int(hash,16)
    c = (a ^ b) % 0xffffffffffffffffffffffffffffffff
    # print path, hash, a, b, c
    return uuid.UUID(int=c)

if __name__ == "__main__": 
    if len(sys.argv) < 3:
        sys.exit('Usage: scripts/genxid.py path hash-object')
    print genxid(sys.argv[1], sys.argv[2])

