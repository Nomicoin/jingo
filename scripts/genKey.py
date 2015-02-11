#!/usr/bin/env python

import os,base64

print base64.urlsafe_b64encode(os.urandom(30))
