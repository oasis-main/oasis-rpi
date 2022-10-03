//Other people's hard work
use pyo3::prelude::*;
use rppal::gpio::Gpio;
use rppal::gpio::OutputPin;
use rppal::gpio::Error;
use std::any::TypeId;


// A Python-ready GPIO output class
#[pyclass]
struct GpioOut{out: OutputPin}

// Behavior of the GPIO output class
#[pymethods]
impl GpioOut { 
    #[new]
    fn new(pin: u8) -> PyResult<Self> { //this is like __init__()
        let mut io_pin = Gpio::new()?.get(pin)?.into_output();
        let mut output = GpioOut{out: io_pin};
        Ok(output)
    }
    
    fn set_high(&mut self){
        self.out.set_high();
    }

    fn set_low(&mut self){
        self.out.set_low();
    }

    fn clean_up(&mut self){
        drop(self.out);
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
    m.add_class::<GpioOut>()?;
    Ok(())
}