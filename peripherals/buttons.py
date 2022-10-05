import sys

#set proper path for modules
sys.path.append('/home/pi/oasis-grow')

import rusty_pins

def new(bcm_pin_number: int):
    pin = rusty_pins.GpioIn(bcm_pin_number)
    return pin

if __name__ == "__main__":
    print("This is a unit test for buttons.")
    test = new(27) #this is normally the connect_device button
    
    print("Are we initialized?")
    print(test.check_low())
    
    print("Cool. Now press the button.")

    while True:
        if test.check_high():
            print("Button press detected!")
            break
    