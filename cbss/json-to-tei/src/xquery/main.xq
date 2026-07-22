xquery version "3.1";

import module namespace zotero2tei="http://syriaca.org/zotero2tei";

declare default element namespace "http://www.tei-c.org/ns/1.0";
(: TODO: defaults for I/O vars? :)
(: declare variable $input-directory as xs:string external;
 :)
declare variable $input-file as xs:string external;

declare variable $output-directory as xs:string external;

declare variable $path-to-zotero-config as xs:string external;

declare variable $zotero-config := doc($path-to-zotero-config);

let $json := json-doc($input-file, map {"format": "xquery"})
let $newRecord := zotero2tei:build-new-record($json, $json?key, 'json', $zotero-config)

let $fileName := $json?key||".xml"

return (
  file:create-dir($output-directory),
  file:write($output-directory||$fileName, $newRecord)
)