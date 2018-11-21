#file used for setup on ADHC server

#!/usr/bin/python
#PROJECT_DIR = '/srv/www/adhc/apps/testapp2/'

#activate_this = os.path.join(PROJECT_DIR, 'venv/bin', 'activate_this.py')

#activate_this = '/srv/www/adhc/apps/testapp2/venv/bin/activate_this.py'
#execfile(activate_this, dict(__file__=activate_this))



activate_this = '/srv/www/millmarginalia/venv/bin/activate'
#with open(activate_this) as file_:
#    exec(file_.read(), dict(__file__=activate_this))

#sys.path.insert(0, '/srv/www/adhc/apps/testapp2')






#sys.path.append(PROJECT_DIR)


import sys
sys.path.insert(0, '/srv/www/millmarginalia')

from main import app as application
from werkzeug.debug import DebuggedApplication
application = DebuggedApplication(application, True)
