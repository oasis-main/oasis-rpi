use std::time::Duration;
use pyo3::prelude::*;
use subprocess::{Popen,PopenConfig,ExitStatus};

// A safe, Python-ready subprocess class for spawning & managing unix children
#[pyclass(unsendable)]
struct Open{process: Popen}

// Behavior of the subprocess class
#[pymethods]
impl Open { 
    #[new] // call this from python with rusty_pipes.Ropen(pin#)
    fn new(arg_list: Vec<String>) -> Self { //this is like python __init__()
        let mut sub_proc = Popen::create(&arg_list[..], PopenConfig::default()).unwrap();
        sub_proc.detach();
        Open{process: sub_proc}
    }
    
    fn wait(&mut self){ //don't do whatever's next until the child has exited
        self.process.wait().unwrap();
    }

    fn wait_timeout(&mut self, secs: u64){ //moves on after some time
        let seconds = Duration::new(secs, 0); //but DOES NOT KILL the child proc
        self.process.wait_timeout(seconds).unwrap();
    }

    fn exited(&mut self) -> bool{ //has it exited?
        let value = self.process.poll();
        if let Some(_exit_status) = value {
            true //yes -> return true
        } else {
            false //no -> return false
        }
    }

    fn exit_code(&mut self) -> u32{
        let value = self.process.exit_status();
        if let Some(ExitStatus::Exited(exit_status)) = value {
            exit_status
        } else {
            1000 //obviously a failure lol
        }
        
    }

    fn terminate(&mut self){ //be careful with calling this
        self.process.terminate().unwrap();
    }

}

// A Python-ready GPIO I/O module
#[pymodule]
fn rusty_pipes(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_class::<Open>()?;
    Ok(())
}