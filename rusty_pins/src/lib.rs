use pyo3::prelude::*;
use rust_gpiozero::{Button, OutputDevice};

// A wrapper "button" struct
#[pyclass]
struct ButtonInput {
    buttn: Box<Button>
}



#[pymethods] 
impl ButtonInput { 
    #[new]
    fn new(pin: u8) -> Self { //this is like __init__()
        ButtonInput {buttn: Box::new(Button::new(pin))
        }
    }

    fn is_pressed(&self){
        self.buttn.value();
    }

    fn await_press(&mut self){
        self.buttn.wait_for_press(None);
    }

    fn close(self){
        self.buttn.close();
    }

}

#[pymodule]
fn rusty_pins(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_class::<ButtonInput>()?;
    Ok(())
}