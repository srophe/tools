from BaseXClient import BaseXClient
import json, yaml, argparse, os


"""
INSTRUCTIONS:
- basex must be installed
- use the terminal to run `basexhttp -c PASSWORD` to set the admin password to 'admin' and start a basex server
- install 
- run via commandline. For now it defaults to the config.yaml file
"""
# Set up and parse command line arguments
parser = argparse.ArgumentParser(
                    prog='Syriaca Maintenance',
                    description='Python wrapper for running Syriaca.org maintenance scripts')
# TODO: add any arguments, e.g. allow specifying a different config, etc.
args = parser.parse_args()

config = []
with open("config.yaml", mode="r") as fh:
    config = yaml.safe_load(fh)


"""
Set up BaseX Session and Query
"""
session = BaseXClient.Session('localhost', 1984, 'admin', 'admin')



# execute the commands to set up the options
print("Setting up Basex. Running commands...")
for cmd in config["commands"]:
    session.execute(cmd)
    print(f"Ran command `{cmd}`. Successful")

print("~~~~~~~~~~~~~~~~~~~~~~~~~")
try:
    # TODO: give some feedback and interaction (maybe with some flags for levels of interaction, e.g. I can pass a --quiet flag to run all without any messages or something)
    print("\nRunning XQuery scripts...\n")
    for script in config["scripts"]:
        # Initial logging and user input to ensure this script should be run in this pass
        print(f"Preparing to run {script['path']}.")
        print(f"Description: {script['description']}")
        print("The following variables bindings will be passed to the script:")
        for variable in script["variables"]:
                print(f"\t{variable['name']}={variable['value']}")
        run_skip_end = input("\nOkay to run this script? (run / skip / end): ").lower()
        while(run_skip_end not in ["run", "skip", "end"]):
            run_skip_end = input("Unrecognized option. Okay to run this script? (run / skip / end): ").lower()
        if(run_skip_end == "skip"):
            print(f"Script {script['path']} was skipped by user.\n")
            continue
        if(run_skip_end == "end"):
            print(f"Program terminated. Script {script['path']} and subsequent scripts were skipped by user.\n")
            break
        # otherwise go ahead with running the script
        print(f"Running script {script['path']}\n")
        
        with open(script["path"], mode="r") as fh:
            # load the query into the BaseX session
            query = session.query(fh.read())

            # Bind external variables declared in the config file
            for variable in script["variables"]:
                query.bind(variable["name"], variable["value"])

            # TODO: override commands with query-specific ones (would mean moving the main commands down to re-run after each query)
            
            # run the query
            # TODO: what happens with output?
            query.execute()
            print(f"Script {script['path']} ran successfully.\n")

finally:
    # close session
    if session:
        session.close()