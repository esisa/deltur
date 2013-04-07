import os, sys
sys.path.insert(0, os.path.dirname(__file__))
print os.path.dirname(__file__) + "/delturapp"

import logging
logging.basicConfig()

from delturapp.app import app as application

