//Other people's hard work
use pyo3::prelude::*;
use rppal::gpio;

// A Python-ready GPIO output class
#[pyclass]
struct GPIO_Out {out: gpio::OutputPin}

// Behavior of the GPIO output class
#[pymethods] 
impl GPIO_Out { 
    #[new]
    fn new(pin: u8) -> Self { //this is like __init__()
        GPIO_Out{out: gpio::Gpio::new().get(pin).into_output()}
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
    m.add_class::<GPIO_Out>()?;
    Ok(())
}