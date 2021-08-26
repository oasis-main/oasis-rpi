import sys
from subprocess import Popen

#set proper path for modules
sys.path.append('/home/pi/oasis-grow')
sys.path.append('/usr/lib/python37.zip')
sys.path.append('/usr/lib/python3.7')
sys.path.append('/usr/lib/python3.7/lib-dynload')
sys.path.append('/home/pi/.local/lib/python3.7/site-packages')
sys.path.append('/usr/local/lib/python3.7/dist-packages')
sys.path.append('/usr/lib/python3/dist-packages')

patch = Popen(["chmod" ,"+x", "/home/pi/oasis-grow/scripts/update_patch.sh"])
patch.wait()

patch = Popen("source /home/pi/oasis-grow/scripts/update_patch.sh", shell = True)
output, error = patch.communicate()

print("Successfully ran commands to patch-in latest update")

