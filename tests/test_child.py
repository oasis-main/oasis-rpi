import sys
import time
import signal

def graceful_exit(*args): #sigterm function should always be defined with optional args
    #print("Received signal: " + str(signum) )
    print("Alright, I'm gonna bow out. Peace fools.")
    print("Cleaning up before I go.")
    sys.exit()


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, graceful_exit)
    print("Hello!")
    time.sleep(10)
    print("Goodbye!")
