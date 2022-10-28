use pyo3::prelude::*;
use serde_json::*;

/// lock(lock_filepath, resource_key, /)
/// --
///
/// Obtain lock for a resource
#[pyfunction]
fn lock(lock_filepath: String, resource_key: String) { 
    for _x in 0..100{ //start attempting to load & write the lock
    
        //load the lock file into json
        let lock_obj = {
            // Load the first file into a string.
            let text = std::fs::read_to_string(&lock_filepath);

            match text {
                Ok(json) => {// Parse the string into a dynamically-typed JSON structure.
                    serde_json::from_str::<Value>(&json)},
                Err(_) => {panic!()}
            }

        };
        
        match lock_obj {
            Ok(mut locks) => {//lock this resource in the JSON structure
                
                locks[&resource_key] = Value::Number(Number::from(1));
                //write the new data back to the json file
            
                // Save the JSON structure into the other file.
                std::fs::write(&lock_filepath, serde_json::to_string_pretty(&locks).unwrap()).unwrap()
            },
            
            Err(_) => {
                continue
            }


        }

        break
    }

}

/// unlock(lock_filepath, resource_key, /)
/// --
///
/// Obtain lock for a resource, should fail if lock is not held
#[pyfunction]
fn unlock(lock_filepath: String, resource_key: String) { //equivalent to reset_lock (singular)
    for _x in 0..100{ //start attempting to load & write the lock
    
        //load the lock file into json
        let lock_obj = {
            // Load the first file into a string.
            let text = std::fs::read_to_string(&lock_filepath);

            match text {
                Ok(json) => {// Parse the string into a dynamically-typed JSON structure.
                    serde_json::from_str::<Value>(&json)},
                Err(_) => {panic!()}
            }

        };
        
        match lock_obj {
            Ok(mut locks) => {//lock this resource in the JSON structure
                
                locks[&resource_key] = Value::Number(Number::from(0));
                //write the new data back to the json file
            
                // Save the JSON structure into the other file.
                std::fs::write(&lock_filepath, serde_json::to_string_pretty(&locks).unwrap()).unwrap()
            },
            
            Err(_) => {
                continue
            }


        }

        break
    }
}

/// reset_locks(lock_filepath, /)
/// --
///
/// Reset all locks
#[pyfunction]
fn reset_locks(lock_filepath: String) {
    for _x in 0..100{ //start attempting to load & write the lock
    
        //load the lock file into json
        let lock_obj = {
            // Load the first file into a string.
            let text = std::fs::read_to_string(&lock_filepath);

            match text {
                Ok(json) => {// Parse the string into a dynamically-typed JSON structure.
                    serde_json::from_str::<Value>(&json)},
                Err(_) => {panic!()}
            }
        };
        
        match lock_obj {
            
            Ok(mut locks) => {//lock this resource in the JSON structure
                
                // Get the number of elements in the lock object.
                let elements = {
                    locks.as_object_mut().unwrap()
                };

                for element in elements{
                    //lock this resource in the JSON structure
                    *element.1 = Value::Number(Number::from(0));  
                }

                // Save the JSON structure into the other file.
                std::fs::write(&lock_filepath, serde_json::to_string_pretty(&locks).unwrap()).unwrap();
            },

            Err(_) => {
                continue
            }
        }

        break
    }

        
}
    

/// A Python module implemented in Rust.
#[pymodule]
fn rusty_locks(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(lock, m)?)?;
    m.add_function(wrap_pyfunction!(unlock, m)?)?;
    m.add_function(wrap_pyfunction!(reset_locks, m)?)?;
    Ok(())
}