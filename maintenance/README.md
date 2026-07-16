# Syriaca Routine Maintenance Scripts

This directory contains routine maintenance scripts that can be run against the Syriaca.org dataset via a Python wrapper. The following guides users through the set up, execution, and customization of this wrapper.

# Installation

To run the XQueries, install the latest release of [BaseX](https://basex.org/).

Installing Python dependencies relies on [Poetry](https://python-poetry.org/), a Python tool for package dependency management. Please refer to Poetry documentation for guidance on setting up this tool on your system. In particular, it should be set up as a Python CLI application via something like `pipx`.

Once Poetry has been added, it can be used to set up a virtual environment and install the dependencies for the Zotero dump script.

Clone the [Syriaca tools](https://github.com/srophe/tools/) repository, then navigate to it in your terminal (e.g., `cd ~/Documents/GitHub/tools`). Finally, navigate to this folder:

`cd maintenance`

 and run:

`poetry install`

This only needs to be done once, and Poetry will create a virtual environment and install the needed dependencies.

You can verify that it was successful by running

`poetry run python maintenance.py --help`

This should print the following:

```
usage: Syriaca Maintenance [-h] [-c CONFIG]

Python wrapper for running Syriaca.org maintenance scripts

options:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        Path to the configuration file (default: config.yaml)
```

# Set up and Usage

Running the XQueries via the Python wrapper leverages BaseX's client/server architecture, so to run these scripts a local BaseX server must be running.

In a terminal window, run `basexhttp -c PASSWORD` to run a local server. You will be prompted to enter a password, which should be set to `admin`. (N.B.: As the server only runs locally, and is only used to allow the Python client to interact with it, the password does not need to be secret - 'admin' is hard-coded in the Python client at present)

In a separate terminal window, navigate to the current folder, e.g. `cd maintenace`.

To run the script, use the following command:

`poetry run python maintenance.py`

The script will attempt to execute the XQuery scripts (defined in the configuration file, on which see below) in sequence. It will log to the user each script, and can be prompted to skip or prematurely end as needed.

## XQueries

At present, only updating XQueries (i.e., those that change the target XML files directly) or those which save a file to disk are supported.

# Configuration

A configuration file (e.g., `config.yaml`) is provided to the script to control BaseX functionality and which XQueries are executed, their sequence, etc. 

The path to this file can be specified with the `-c` flag, e.g. `poetry run python maintenance.py -c /path/to/config.yaml`. By default (i.e., not using that flag), this will be set to the config file in the current directory (`config.yaml`).

The following options are available and should be defined in that file:

- `commands`: This parameter takes a collection of [BaseX commands](https://docs.basex.org/main/Commands). Common use cases are to allow/disallow writing updating expressions to disk (`SET WRITEBACK`), or to control serialization and export options (indentation, XML declaration, etc.). **Note that these commands are set for _all_ of the scripts**
- `scripts`: **Required**. This parameter contains mappings of information about the individual XQuery scripts that will be executed by the Python wrapper. This includes the following options:
  - `path`: **Required**. The file path of the XQuery script. This can be relative to the `maintenance` directory, or an absolute path
  - `description`: An optional human-readable description of what the referenced XQuery script does
  - `variables`: Used to bind values to the external variables declared in the XQuery script. These are often used to provide file paths to the individual scripts for I/O requirements. Each instance must have a `name`, which is the XQuery variable name; a `value`, which is the value to be bound to the variable; and optionally a description explaining what the variable is.


# Troubleshooting Notes

The following are common errors, and how to resolve them.

- `ConnectionRefusedError: [Errno111] Connection refused`: Ensure the BaseX server is running (see above under "Set up and Usage")
- Errors related to importing the functx library. This can occur if the functx library is not installed to your local BaseX repository. Run the following command, either by including it in the `commands` list in the configuration file or running it in you BaseX GUI client: `REPO INSTALL https://files.basex.org/modules/expath/functx-1.0.xar`

# Areas of Future Development

- [ ] Include the basex server config in the config file, just in case someone wants to change this
- [ ] Add a CLI flag that controls whether you get prompted to run each script or not (e.g., `-q --quiet`)
    - the trick here is reworking the logging functionality into a function that can be called or not based on the argument. And also some of the logic of breaking vs continuing, etc. would be handled by that function
- [ ] Allow scripts to override commands (would need to re-run the general commands each time, which would be an issue for the REPO INSTALL commands...maybe split those into a separate section of the config)
    - would have a commands parameter for each script, which would be run for that script
    - would probably have a flag or something on each of the main commands that would indicate 'override' vs 'one-time' (maybe it's based on whether it's SET vs something like REPO INSTALL?)