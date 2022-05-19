import os, traceback, sys

#set proper path for modules
sys.path.append('/home/pi/oasis-grow')
sys.path.append('/home/pi/oasis-grow/utils')
sys.path.append('/usr/lib/python37.zip')
sys.path.append('/usr/lib/python3.7')
sys.path.append('/usr/lib/python3.7/lib-dynload')
sys.path.append('/home/pi/.local/lib/python3.7/site-packages')
sys.path.append('/usr/local/lib/python3.7/dist-packages')
sys.path.append('/usr/lib/python3/dist-packages')

import concurrent_state as cs

def full_stack():
    exc = sys.exc_info()[0]
    stack = traceback.extract_stack()[:-1]  # last one would be full_stack()
    if exc is not None:  # i.e. an exception is present
        del stack[-1]       # remove call of full_stack, the printed exception
                            # will contain the caught exception caller instead
    trc = 'Traceback (most recent call last):\n'
    stackstr = trc + ''.join(traceback.format_list(stack))
    if exc is not None:
         stackstr += '  ' + traceback.format_exc().lstrip(trc)
    return stackstr

#Decorator: https://www.geeksforgeeks.org/error-handling-in-python-using-decorators/
def Error_Handler(func):
    def Inner_Function(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except KeyboardInterrupt as k:
            print("Keyboard Interrupt")
            cs.write_state("/home/pi/oasis-grow/configs/device_state.json", "device_error", str(k))
        except TypeError as t:
            print(f"{func.__name__} wrong data types.")
            full_stack()
            cs.write_state("/home/pi/oasis-grow/configs/device_state.json", "device_error", str(t))
        except Exception as e:
            full_stack()
            cs.write_state("/home/pi/oasis-grow/configs/device_state.json", "device_error", str(e))
    return Inner_Function

