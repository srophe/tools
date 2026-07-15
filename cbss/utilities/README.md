# CBSS Utilities and Maintenance Scripts

The scripts in this folder are small utility scripts that are used occasionally to manage the dataset for the [Comprehensive Bibliography on Syriac Studies](https://syriaca.org/cbss).

**As most of these run on the Zotero desktop client, please be _very_ careful when running them since changes are not easily reversible**

- `deprecate.js`: Runs in the Zotero client; prepends `[Deprecated] ` to the title of _selected_ records (i.e. select the records in the Zotero pane prior to running the script). **At present it does not add the the `_deprecated` tag**. It will avoid adding a duplicate `[Deprecated] ` prefix, so you can safely run this against already-deprecated records.
    - Original Gist: https://gist.github.com/wlpotter/37dc148565cdcda1a0f97ea275895e84
- `uris-to-extra-field.js`: Runs in the Zotero client. Adds to the Extra field of _selected_ records the Zotero URI and the Syriaca CBSS URI (i.e., `http://syriaca.org/cbss/{id}`). It will avoid duplicating if these keys already exist in the extra field.