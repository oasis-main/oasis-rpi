import sys
import time
import signal

def graceful_exit(signum, frame):
    #print("Received signal: " + str(signum) )
    print("Alright, I'm gonna bow out. Peace fools.")
    print("Cleaning up before I go.")
    sys.exit(0)

if __name__ == '__main__':
    signal.signal(signal.SIGTERM, graceful_exit)
    print("Hello!")
    time.sleep(10)
    print("Goodbye!")
