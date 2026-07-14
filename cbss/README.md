# Workflows, Scripts, and Tools for The Comprehensive Bibliography on Syriac Studies

This directory of the Syriaca tools repository includes workflows, scripts, tools, and other information useful for publishing and working with data in the [Comprehensive Bibliography on Syriac Studies](http:syriaca.org/cbss).

Zotero Library: https://www.zotero.org/groups/4861694/
Website: https://syriaca.org/cbss

# Publishing Data to CBSS

The following documents the publication pipeline for CBSS data.

1. Add data records to the Zotero Library.
    - This requires admin-level access to that library.
    - For core Syriaca editors/projects, please add data as the `cbss_admin` user account
    - For collaborating projects, e.g. _A Guide to John of Ephesus_, please request a project-specific user account from the Syriaca.org editors.
    - More details and guidelines for contributing to the CBSS Zotero library may be found in the [Contributor Guidelines for CBSS](https://github.com/srophe/syriaca-data/wiki/Contributor-Guidelines-for-the-Comprehensive-Bibliography-on-Syriac-Studies)
2. Download CBSS Zotero data from the Zotero Web API
    - Data should be downloaded using the bulk download script **TBD: put that script in this repo**
3. Process and deposit downloaded JSON data into the `syriaca-data` repository
    - The bulk download script chunks downloaded JSON records into batches, but they need to be stored in `syriaca-data` as individual documents named for the Zotero Item Key
    - **TBD: script to do this...**
    - The output of these records should go into `data/cbss/json/` within the `syriaca-data` repository
4. Run JSON to TEI XML transform
    - The GitHub repository for this code is in https://github.com/srophe/zotero2bibl/
    - **TBD: Refer to that repository's documentation for steps to run this code**
5. Store output TEI XML data in the `syriaca-data` repository
    - Either set the output directory for the TEI XML transform, or copy/paste the resulting XML files into that directory


# Repository Structure

The primary purpose of this directory is to store maintenance scripts, of varying complexity, useful for the management and publication of CBSS data. These scripts may be found in the `scripts` folder. Some will be further nested in independent directories, depending on their level of complexity and/or their dependency on additional modules/packages. See the `scripts` directory for further information.