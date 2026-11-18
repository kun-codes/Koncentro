use std::fs;
use std::num::NonZeroU32;
use std::path::PathBuf;

use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};

struct Proc {
    pid: NonZeroU32,
    exe: Option<PathBuf>,
    name: String,
    cmdline: Vec<String>,
}

impl app_rummage::Process for Proc {
    fn pid(&self) -> NonZeroU32 {
        self.pid
    }
    fn executable_path(&self) -> Option<PathBuf> {
        self.exe.clone()
    }
    fn name(&self) -> &str {
        &self.name
    }
    fn cmdline(&self) -> &[String] {
        &self.cmdline
    }
}

fn scan_processes() -> Vec<Proc> {
    let mut procs = Vec::new();
    let entries = match fs::read_dir("/proc") {
        Ok(e) => e,
        Err(_) => return procs,
    };
    for entry in entries.flatten() {
        let file_name = entry.file_name();
        let Some(pid_str) = file_name.to_str() else { continue };
        let Ok(num) = pid_str.parse::<u32>() else { continue };
        let Some(pid) = NonZeroU32::new(num) else { continue };

        let exe = fs::read_link(format!("/proc/{pid}/exe")).ok().map(|p| {
            let s = p.to_string_lossy();
            PathBuf::from(s.strip_suffix(" (deleted)").unwrap_or(&s))
        });


        let name = fs::read_to_string(format!("/proc/{pid}/comm"))
            .map(|s| s.trim().to_string())
            .unwrap_or_default();


        let cmdline = fs::read(format!("/proc/{pid}/cmdline"))
            .map(|data| {
                data.split(|&b| b == 0)
                    .filter(|tok| !tok.is_empty())
                    .map(|tok| String::from_utf8_lossy(tok).into_owned())
                    .collect()
            })
            .unwrap_or_default();

        procs.push(Proc { pid, exe, name, cmdline });
    }
    procs
}

#[pyfunction]
fn installed(py: Python<'_>) -> PyResult<Py<PyAny>> {
    let dict = PyDict::new(py);
    for (id, app) in app_rummage::installed_apps() {
        dict.set_item(id.to_string(), app.name.to_string())?;
    }
    Ok(dict.into_any().unbind())
}

#[pyfunction]
fn running(py: Python<'_>) -> PyResult<Py<PyAny>> {
    let available = app_rummage::installed_apps();
    let processes = scan_processes();

    let list = PyList::empty(py);
    for (app, pids) in app_rummage::running_apps(&available, &processes) {
        let dict = PyDict::new(py);
        dict.set_item("id", app.id.to_string())?;
        dict.set_item("name", app.name.to_string())?;
        let pid_list = PyList::empty(py);
        for pid in pids {
            pid_list.append(pid.get())?;
        }
        dict.set_item("pids", pid_list)?;
        list.append(dict)?;
    }
    Ok(list.into_any().unbind())
}

#[pymodule]
fn app_rummage_py(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(installed, m)?)?;
    m.add_function(wrap_pyfunction!(running, m)?)?;
    Ok(())
}
