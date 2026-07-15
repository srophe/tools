/*
author: William L. Potter
version: 1.0

This JS will update the extra field for selected records in a Zotero library.
It adds to the extra field the Zotero URI for the item, as well as the Syriaca URI
It only adds these properties if they do not already exist

To run the script,
1. Open the Zotero desktop client
2. Select the items you would like to run the script on
3. From the menu, open the Tools > Developer > Run JavaScript modal
4. Select the "Run as async function" option
5. Paste this full script into the Code window
6. Click "Run" (ctrl/cmd + R)
7. The items will be saved, and the updated extra fields will be printed to the "Return value" pane
*/

/*
Update the following constants to alter the URI base and/or extra field keys
*/
const CBSS_URI_BASE = "http://syriaca.org/cbss/";
const CBSS_URI_EXTRA_KEY = "SyriacaURI";
const ZOTERO_URI_BASE = "https://www.zotero.org/groups/4861694/items/";
const ZOTERO_URI_EXTRA_KEY = "ZoteroURI";


var pane = Zotero.getActiveZoteroPane();
var items = pane.getSelectedItems();

var extra_data = [];

for (let i = 0; i < items.length; i++) {
    var extra = items[i].getField('extra');
    // skip if the extra field already contains both URIs
    if (extra.includes(ZOTERO_URI_EXTRA_KEY) && 
        extra.includes(CBSS_URI_EXTRA_KEY)) continue;
    
    //get the item key and construct the Zotero and CBSS URIs from it
    var itemKey = items[i].getField('key');
    zot_uri = ZOTERO_URI_BASE + itemKey;
    cbss_uri = CBSS_URI_BASE + itemKey;
    
    //create the Zotero URI key if does not exist, otherwise leave empty
    if (!(extra.includes(ZOTERO_URI_EXTRA_KEY))) {
        prepend_to_extra = ZOTERO_URI_EXTRA_KEY + ": " + zot_uri;
        if (!(extra.includes(CBSS_URI_EXTRA_KEY))) {
            prepend_to_extra += ("\n" + CBSS_URI_EXTRA_KEY + ": " + cbss_uri);
        }
    }
    else {
        if (!(extra.includes(CBSS_URI_EXTRA_KEY))) {
            prepend_to_extra = CBSS_URI_EXTRA_KEY + ": " + cbss_uri;
        }
        else {
            prepend_to_extra = ""
        }
    }
    
    
    // prepend new line if extra is non-empty
    if (extra != "") {
        extra = "\n" + extra
    };
    
    extra = prepend_to_extra + extra;
    extra_data += extra;
    items[i].setField('extra', extra);
    await items[i].saveTx();
}
return extra_data;