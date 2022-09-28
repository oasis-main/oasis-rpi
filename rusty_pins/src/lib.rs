use pyo3::prelude::*;
use rust_gpiozero::{Button, Debounce};

// A wrapper "button" struct
#[pyclass]
struct ButtonInput {
    buttn: Button
}

#[pymethods] //this is like __init__()
impl ButtonInput {
    #[new]
    fn new(value: i32) -> Self {
        Button_Input { buttn: Button::new(value).debounce(Duration::from_millis(100))
         // Adds debouncing so that subsequent presses within 100ms don't trigger a press
        }
    }

    fn is_pressed(&self){
        self.buttn.value()
    }

    fn await_press(&mut self){
        self.buttn.wait_for_press(None)
    }

    fn close(self){
        self.buttn.close()
    }

}

#[pymodule]
fn rusty_pins(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_class::<ButtonInput>()?;
    Ok(())
}