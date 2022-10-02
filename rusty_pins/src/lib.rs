use pyo3::prelude::*;

use std::error::Error;
use std::thread;
use std::time::Duration;

use rppal::gpio::Gpio;

// A wrapper "button" struct
#[pyclass]
struct GPIO_out {input: Gpio}

#[pymethods] 
impl GPIO_out { 
    #[new]
    fn new(pin: u8) -> Self { //this is like __init__()
        Gpio::new()?.get(pin)?.into_output()
    }
    
    fn set_high(&mut self){
        self.set_high();
    }

    fn await_signal(&mut self){
        self.set_low();
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