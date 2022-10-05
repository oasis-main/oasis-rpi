//Other people's hard work
use pyo3::prelude::*;
use rppal_w_frontend::gpio::Gpio;
use rppal_w_frontend::gpio::OutputPin;
use rppal_w_frontend::gpio::InputPin;

// A Python-ready GPIO output class
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

}

// A Python-ready GPIO input class
#[pyclass(unsendable)]
struct GpioIn{input: InputPin}

// Behavior of the GPIO input class
#[pymethods]
impl GpioIn { 
    #[new] // call this from python with rusty_pins.GpioOut(pin#)
    fn new(pin: u8) -> Self { //this is like python __init__()
        let io_pin = Gpio::new().unwrap().get(pin).unwrap().into_input();
        GpioIn{input: io_pin}
    }

    fn check_high(&self) -> bool {
        self.input.is_high()
    }

    fn check_low(&self) -> bool {
        self.input.is_low()
    }
}

// A Python-ready GPIO input class
#[pymodule]
fn rusty_pins(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_class::<GpioOut>()?;
    m.add_class::<GpioIn>()?;
    Ok(())
}