//Other people's hard work
use pyo3::prelude::*;
use rppal::gpio::*;

//We're only doing outputs this way, as peripheral reads in rust are unsafe
//The python implementation for hardware peripheral reads is actually better for raspi
use rppal::gpio::OutputPin;

// A safe, Python-ready GPIO output class that operates on the hardware level
#[pyclass(unsendable)]
struct GpioOut{output: OutputPin}

// Behavior of the GPIO output class
#[pymethods]
impl GpioOut { 
    #[new] // call this from python with rusty_pins.GpioOut(pin#)
    fn new(pin: u8) -> Self { //this is like python __init__()
        let io_pin = Gpio::new().unwrap().get(pin).unwrap().into_output();
        GpioOut{output: io_pin}
    }
    
    fn set_high(&mut self){
        self.output.set_high();
    }

    fn set_low(&mut self){
        self.output.set_low();
    }

    fn is_high(&mut self){
        self.output.is_set_high();
    }

    fn is_low(&mut self){
        self.output.is_set_low();
    }
}

// A Python-ready GPIO I/O module
#[pymodule]
fn rusty_pins(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_class::<GpioOut>()?;
    Ok(())
}
