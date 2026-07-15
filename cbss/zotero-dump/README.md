# Zotero Data Dump

This python script can be used to create a dump of Zotero records. It runs in parallel using the [asyncio](https://docs.python.org/3/library/asyncio.html) and [aiohttp](https://docs.aiohttp.org/en/stable/index.html) Python modules. These features enable more efficient execution across large libraries, a requirement for the initial development context of supporting the publication pipeline of the [Comprehensive Bibliography on Syriac Studies](https://syriaca.org/cbss).

This document provides information for installing and using this script, as well as 

# Installation

The preferred installation method is to use [Poetry](https://python-poetry.org/), a Python tool for package dependency management. Please refer to Poetry documentation for guidance on setting up this tool on your system. In particular, it should be set up as a Python CLI application via something like `pipx`.

Once Poetry has been added, it can be used to set up a virtual environment and install the dependencies for the Zotero dump script.

Clone the [Syriaca tools](https://github.com/srophe/tools/) repository, then navigate to it in your terminal (e.g., `cd ~/Documents/GitHub/tools`). Finally, navigate to this folder:

`cd cbss/zotero-dump`

 and run:

`poetry install`

This only needs to be done once, and Poetry will create a virtual environment and install the needed dependencies.

# Usage

Ensure that Poetry has correctly installed the dependencies by running (from the `zotero-dump` folder): `poetry run python src/dump.py --help`. This should return:

```
usage: dump.py [-h] [-c CONFIG] [-e]

options:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        Path to the config JSON (or YAML) file
  -e, --errors          Whether to re-run just on the errors found in the log file
```

As can be seen from the options list, this script requires specifying a JSON or YAML configuration file. The following section details the required and optional fields to include in that file. An example configuation file can be seen in this repository (`config.yaml`); it is _not recommended_ to store the configuration file under version control to avoid inadvertently commiting one's private API key.

The script can be run with:

`poetry run python src/dump.py -c /path/to/config.yaml`

## Configuration File

A configuration file is required, with the following **required** options:

- `zotero_api_base`: **Required**. Must be the Zotero API base URL for the requests. It is strongly recommended to include `/top` to ignore attached/child notes. Example: `https://api.zotero.org/groups/4861694/items/top`
- `session_headers`: Used to set the shared headers for the full client session. Must be a nested JSON object or YAML mapping, where the key:value pairs are the HTTP headers to be passed. The following are recommended:
  - `Zotero-API-Version: "3"`: Recommended by the [Zotero API documentation](https://www.zotero.org/support/dev/web_api/v3/basics#api_versioning).
  - `Zotero-API-Key: $$$$$$$$`: Required for private libraries and groups; recommended for public libraries and groups as a courtesy to clearly identify yourself when interacting with the API. **N.B.: If you use this header, do not store the configuration file under version control in this repository to avoid exposing your private API key!**
- `limit_interval`: **Required**. Sets the maximum number of results to return for a single request. Must be an integer between 1-100; values between 50 and 100 are recommended. This controls the `?limit` parameter in requests; see the [Zotero API documentation](https://www.zotero.org/support/dev/web_api/v3/basics#sorting_and_pagination) for more information.
- `start_at`: **Required**. Sets the record number from which to begin requesting records. To download all records, must be set to 0. This parameter can be used, for example, to manually execute the data dump in batches. It sets the `?start` parameter for the initial request (subsequent requests increment this parameter automatically); see [Zotero API documentation](https://www.zotero.org/support/dev/web_api/v3/basics#sorting_and_pagination) for more information.
- `max_records`: Optionally set the total number of records to return. Along with `start_at`, this can be used to manually execute the data dump in batches. When absent, the script will use the total number of items in the library as the maximum.
- `since`: Optionally this parameter lets you specify a library version, allowing the script to only return records modified 'since' that version. When absent, the script will download the full library. This field populates the `?since` parameter; see [Zotero API documentation](https://www.zotero.org/support/dev/web_api/v3/basics#search_parameters) for more information. _N.B.: Downloading results via a 'last modified date' is not currently supported. As a workaround, users can find the library version prior to the modified records they want to download and use the since option (though redownloading the full library may still be more efficient)_
- `total_callers`: **Required**. Controls the number of concurrent API requests. Large numbers can increase the efficiency of the script but may result in more errors returned (e.g., from 'too many requests'); smaller numbers have the inverse effect. Numbers between 4-8 are recommended to balance efficiency and error occurence (though see below for how to re-run the script just on requests that received errors).
- `save_directory`: **Required**. The **full path** to a directory in which returned records should be saved. The script will recursively create directories if they do not exist.
- `file_name_base`: **Required**. Returned records are saved as chunks (based on the `limit_interval`). This option sets what the base filename should be for the saved JSON files, to which will be appended the range (e.g., 0-99, 100-199, etc.). Example: `zotero_dump2026-07-15_`
- `log_path`: **Required**. The **full path** to a directory in which to save the log file. (See below for more information on what this file contains). The script will recursively create directories if they do not exist.
- `log_file_name`: **Required**. The file name for the log file, to be stored at the location specified in the `log_path` option.

## Log File

In addition to the downloaded data, the script will save a log file providing details on the request that was made, its results (e.g., if it was a success or failure), the expected keys of the returned data, and the save directory and filename for those data. For errors, the file will include a description of the error that occurred, if possible.

The log file, as well, is used in processing errors (using the `-e` flag) to resend the requests that failed.

## Retrying Errors

Most errors that occur are due to temporary issues between the request and the server (e.g., too many requests, or a connection timeout). As these types of errors are often resolved by retrying the request after a longer period, the script enables you to re-run just the requests that received errors. The log file (see above) will note which requests were successful and which had errors. The script will also log to the terminal its success rate, e.g. `All 5 API Calls have been made, with 3 successful; 2 error(s). See the log file for full results`. To retry just the requests that returned errors, specify the `-e` flag when calling the script:

`poetry run python src/dump.py -c /path/to/config.yaml -e`

The script will run as normal, but will only make the requests marked as errors in the log file. Note that the config file should not be changed, as it already has the path to the log file containing the errors.

# Areas of Future Development

- [ ] Implement a last modified date filter (somewhat tricky with the concurrent calls/coroutines structure)
- [ ] Allow the other API options to be set in config? (e.g., the include and style options)
    - setting `format` would also require potentially saving it a different way
- [ ] Add max retries and default backoff to the config? (need to figure out how to call these from the tenacity functions)
- [ ] Add a specific check in 429 errors to follow the requested response delay header to override backoffs