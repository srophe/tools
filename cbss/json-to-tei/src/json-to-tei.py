import os
import yaml
import argparse
from BaseXClient import BaseXClient

# TODO:
"""
Oh right, the problem with calling the module function is it relies on the globally-declared variable in that module
that points to the config file, which is hard-coded (technically an external variable with a hard-coded default). And
to change to an external that is passed requires the funky xquery-evaluate that I tried previously.

So maybe change the functions there to pass the variable to it and use that one? and it defaults there?

"""

# Install the XQuery dependencies from the config
# TODO: Error handling.
def install_xquery_packages(session, packages):
    """
    - from the session, get the list
    """
    installed_packages = session.execute("xquery repo:list()")
    for pkg in packages:
        if(f"name=\"{pkg['name']}\"" in installed_packages):
            print(f"Package {pkg['name']} already installed.")
        else:
            print(f"Installing package {pkg['name']}")
            session.execute(f"REPO INSTALL {pkg['location']}")

def run_transform(session, zotero_config, filepath, output_dir):
    with open(config["script"]["path"], mode="r") as fh:
        # load the query into the BaseX session
        query = session.query(fh.read())

        # Bind external variables based on the CLI
        query.bind("$input-file", filepath)
        query.bind("output-directory", output_dir)
        query.bind("path-to-zotero-config", zotero_config)
        return query.execute()

if __name__ == "__main__":
    # Set up and parse command line arguments
    parser = argparse.ArgumentParser(
                        prog='Syriaca Maintenance',
                        description='Python wrapper for running Syriaca.org maintenance scripts',
                        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("-i", "--input", help="Path to the input directory or file to transform")
    parser.add_argument("-o", "--output", help="Path to the output directory where transformed files should be stored")
    parser.add_argument("-c", "--config", help="Path to the configuration file", default="config.yaml")

    args = parser.parse_args()
    config = []
    with open(args.config, mode="r") as fh:
        config = yaml.safe_load(fh)

    print(config["commands"])


    """
    Set up BaseX Session and Query
    """
    # TODO: error handling for all of the setup (session launch, package install, commands)
    print("Setting up Basex.")

    session_config = config["basex_session"]
    session = BaseXClient.Session(session_config["host"], session_config["port"], session_config['user'], session_config["password"])

    """
    Install required XQuery packages to local BaseX install, if needed
    """
    print("Ensuring XQuery packages are installed...")
    # Install the XQuery package
    install_xquery_packages(session, config["packages"])
    
    """
    Run Setup Commands in BaseX Session
    """
    print("Running setup commands...")
     # execute the commands to set up the options
    for cmd in config["commands"]:
        session.execute(cmd)
        print(f"Ran command `{cmd}`. Successful")

    try:
        print("Running XQuery script to transform JSON to TEI records")
        """
        If input is a file, run the script once
        otherwise run it on all xml files in the directory        
        """
        # If a file, run just on that file
        if(os.path.isdir(args.input)):
            for file in os.listdir(args.input):
                # Ignore non-JSON files
                if(file.endswith(".json")):
                   output = run_transform(session=session, 
                                          zotero_config=config["zotero_config"], 
                                          filepath=args.input+file, 
                                          output_dir=args.output)
                   print(output)
        # Otherwise run on the full directory
        elif(os.path.isfile(args.input) and args.input.endswith(".json")):
            output = run_transform(session=session, 
                                    zotero_config=config["zotero_config"], 
                                    filepath=args.input, 
                                    output_dir=args.output)
            print(output)
        else:
            print(f"Input argument, {args.input}, is not a directory or a JSON file.")

    finally:
        # close session
        if session:
            session.close()