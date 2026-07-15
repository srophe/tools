/*

author: William L. Potter
version: 1.0

This JS will add a prefix to the main title field of "[Deprecated] ".
It only adds this prefix to items selected in the main Zotero pane.
It will not add the prefix to records that already have it.

To run the script,
1. Open the Zotero desktop client
2. Select the items you would like to run the script on
3. From the menu, open the Tools > Developer > Run JavaScript modal
4. Select the "Run as async function" option
5. Paste this full script into the Code window
6. Click "Run" (ctrl/cmd + R)
7. The items will be saved, and the item keys will be returned to the "Return value" pane. Errors will also be logged to this pane

*/
let ZoteroPane = Zotero.getActiveZoteroPane();
let selectedItems = ZoteroPane.getSelectedItems();

const deprecatedPrefix = "[Deprecated] ";
const items = [];
for (let i = 0; i<selectedItems.length; i++) {
    // get the title of the item
    let title = selectedItems[i].getField('title');
    //if the title is already deprecated with the prefix, skip it
    if(title.startsWith(deprecatedPrefix)) {
        continue;
    }
    // otherwise prepend to the item's title and save changes
    let deprecatedTitle = deprecatedPrefix + title;
    selectedItems[i].setField('title', deprecatedTitle);
    let itemId = await selectedItems[i].saveTx();
    items.push(itemId); //adds true to the array or logs an error
}
return items;