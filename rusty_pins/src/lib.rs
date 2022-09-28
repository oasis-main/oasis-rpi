use pyo3::prelude::*;
use rust_gpiozero::{Button, Debounce};

/*
Relay code in python: example
    #setup GPIO
    
    GPIO.setmode(GPIO.BCM) #GPIO Numbers instead of board numbers
    water_GPIO = cs.structs["hardware_config"]["equipment_gpio_map"]["water_relay"] #heater pin pulls from config file
    GPIO.setup(water_GPIO, GPIO.OUT) #GPIO setup
    GPIO.output(water_GPIO, GPIO.LOW) #NO relay close = GPIO.HIGH, NO relay open = GPIO.LOW
    GPIO.output(water_GPIO, GPIO.HIGH) #NC relay close = GPIO.LOW, NC relay open = GPIO.HIGH
 */

// A "tuple" struct
#[pyclass]
struct Number(i32);

#[pymethods] //this is like __init__()
impl Number {
    #[new]
    fn new(value: i32) -> Self {
        Number(value)
    }
}

#[pymodule]
fn rusty_pins(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_class::<Number>()?;
    Ok(())
}