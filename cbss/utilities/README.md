# CBSS Utilities and Maintenance Scripts

The scripts in this folder are small utility scripts that are used occasionally to manage the dataset for the [Comprehensive Bibliography on Syriac Studies](https://syriaca.org/cbss).

**As most of these run on the Zotero desktop client, please be _very_ careful when running them since changes are not easily reversible**

For the scripts run within the Zotero desktop client, the user will then need to sync with the web library prior to following the publication steps outlined in this directory's parent directory (i.e., `../README.md`).

- `deprecate.js`: Runs in the Zotero client; prepends `[Deprecated] ` to the title of _selected_ records (i.e. select the records in the Zotero pane prior to running the script). **At present it does not add the the `_deprecated` tag**. It will avoid adding a duplicate `[Deprecated] ` prefix, so you can safely run this against already-deprecated records.
    - Original Gist: https://gist.github.com/wlpotter/37dc148565cdcda1a0f97ea275895e84
- `uris-to-extra-field.js`: Runs in the Zotero client. Adds to the Extra field of _selected_ records the Zotero URI and the Syriaca CBSS URI (i.e., `http://syriaca.org/cbss/{id}`). It will avoid duplicating if these keys already exist in the extra field.
    - Original Gist: https://gist.github.com/wlpotter/7fce58dbc8dd5bd79368925cfc1f1644

The following external scripts and repositories may be of use on rare occasion:

- https://github.com/wlpotter/zotcsv: Used to add data to Zotero records from a CSV file. Only supports simple actions like appending data to the extra field. (contact @wlpotter for help with setting up and running this script)
- https://github.com/wlpotter/sandbox/tree/main/cbss-title-language: The scripts here are used to update the language information of a batch of Zotero records. An XQuery converts a CSV to a JSON file that is then read by a JavaScript (run in the Zotero client) to perform the field updates. (contact @wlpotter for help with these scripts)