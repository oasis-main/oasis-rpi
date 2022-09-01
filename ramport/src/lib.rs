use pyo3::prelude::*;

/// Formats the sum of two numbers as string.
#[pyfunction]
fn lock(a: usize, b: usize) -> PyResult<String> {
    Ok((a + b).to_string())
}

/// Formats the sum of two numbers as string.
#[pyfunction]
fn unlock(a: usize, b: usize) -> PyResult<String> {
    Ok((a + b).to_string())
}
/// Formats the sum of two numbers as string.
#[pyfunction]
fn reset_lock(a: usize, b: usize) -> PyResult<String> {
    Ok((a + b).to_string())
}

/// Formats the sum of two numbers as string.
#[pyfunction]
fn reset_locks(a: usize, b: usize) -> PyResult<String> {
    Ok((a + b).to_string())
}

/// A Python module implemented in Rust.
#[pymodule]
fn ramport(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(lock, m)?)?;
    m.add_function(wrap_pyfunction!(unlock, m)?)?;
    m.add_function(wrap_pyfunction!(reset_lock, m)?)?;
    m.add_function(wrap_pyfunction!(reset_locks, m)?)?;

    Ok(())
}