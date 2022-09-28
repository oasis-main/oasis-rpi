use pyo3::prelude::*;
use rust_gpiozero::{Button, OutputDevice};

// A wrapper "button" struct
#[pyclass]
struct ButtonInput<'a> {
    buttn: &'a mut Button
}

#[pymethods] 
impl ButtonInput { 
    #[new]
    fn new(pin: u8) -> Self { //this is like __init__()
        ButtonInput {buttn: &mut Button::new(pin)
         // Adds debouncing so that subsequent presses within 100ms don't trigger a press
        }
    }

    fn is_pressed(&self){
        self.buttn.value();
    }

    fn await_press(&mut self){
        self.buttn.wait_for_press(None);
    }

    fn close(& mut self){
        self.buttn.close();
    }

}

#[pymodule]
fn rusty_pins(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_class::<ButtonInput>()?;
    Ok(())
}