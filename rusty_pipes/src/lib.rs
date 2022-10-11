use std::time::Duration;
use pyo3::prelude::*;
use subprocess::{Popen,PopenConfig};

// A safe, Python-ready subprocess class for spawning & managing unix children
#[pyclass(unsendable)]
struct Open{process: Popen}

// Behavior of the subprocess class
#[pymethods]
impl Open { 
    #[new] // call this from python with rusty_pipes.Ropen(pin#)
    fn new(arg_list: Vec<String>) -> Self { //this is like python __init__()
        let sub_proc = Popen::create(&arg_list[..], PopenConfig::default()).unwrap();
        Open{process: sub_proc}
    }
    
    fn wait(&mut self){
        self.process.wait().unwrap();
    }

    fn wait_timeout(&mut self, secs: u64){
        let seconds = Duration::new(secs, 0); 
        self.process.wait_timeout(seconds).unwrap();
    }

    fn exited(&mut self) -> bool{
        let value = self.process.poll();
        if let Some(_exit_status) = value {
            true
        } else {
            false
        }
    }

    fn terminate(&mut self){
        self.process.terminate().unwrap();
    }

}

// A Python-ready GPIO I/O module
#[pymodule]
fn rusty_pipes(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_class::<Open>()?;
    Ok(())
}