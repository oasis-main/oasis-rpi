import sys

#set proper path for modules
sys.path.append('/home/pi/oasis-grow')

import rusty_pins

def new(bcm_pin_number: int):
    pin = rusty_pins.GpioIn(bcm_pin_number)
    return pin

if __name__ == "__main__":
    print("This is a unit test for buttons.")
    start = new(5)
    connect = new(6) #this is normally the connect_device button
    action = new(13)

    print("Are we initialized?")
    print(start.check_low())
    print(connect.check_low())
    print(action.check_low())
    
    print("Cool. Now press the button.")

    while True:
        state = start.check_high()
        if  state == True:
            print("Button press detected!")
            break
    