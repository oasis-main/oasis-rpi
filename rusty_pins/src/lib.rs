//Standard stuff
use std::error::Error;
use std::thread;
use std::time::Duration;

// Fancy stuff
use pyo3::prelude::*;
use rppal::gpio::Gpio;

// A Python-ready GPIO output class
#[pyclass]
struct GPIO_out {input: Gpio}

// Behavior of the GPIO output class
#[pymethods] 
impl GPIO_out { 
    #[new]
    fn new(pin: u8) -> Self { //this is like __init__()
        Gpio::new()?.get(pin)?.into_output()
    }
    
    fn set_high(&mut self){
        self.set_high();
    }

    fn set_low(&mut self){
        self.set_low();
    }

    fn clean_up(&mut self){
        self.drop();
    }

}

//fn is_active(&self){
//    self.buttn.value();
//}

//fn await_signal(&mut self){
//    self.buttn.wait_for_press(None);
//}

#[pymodule]
fn rusty_pins(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_class::<GPIO_out>()?;
    Ok(())
}