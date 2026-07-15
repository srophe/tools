xquery version "3.1";

(:
: Module Name: Generate URI and Headwords Table
: Module Version: 1.0
: Copyright: GNU General Public License v3.0
: Proprietary XQuery Extensions Used: None
: XQuery Specification: 08 April 2014
: Module Overview: This main module generates a CSV table from Syriaca.org
:                  records consisting of the entity URI and various headwords
:)

(:~ 
: This main module runs against all Syriaca entities except CBSS records.
: It creates a CSV document mapping the entity URI to the various headwords
:
: @author William L. Potter
: @version 1.0
:)

import module namespace functx="http://www.functx.com"; (:TODO: Import this better so you don't have to have it in the basex repo :)

declare namespace srophe="https://srophe.app";
declare default element namespace "http://www.tei-c.org/ns/1.0";
declare namespace output = 'http://www.w3.org/2010/xslt-xquery-serialization';

declare option output:omit-xml-declaration 'no';
declare option output:indent 'yes';

declare function local:clean-descendant-text($element as node()?)
as xs:string? {
  $element//text()
    => string-join(" ")
    => normalize-space()
};

declare variable $path-to-syriaca-data external;
declare variable $works := collection($path-to-syriaca-data||"data/works/tei/");
declare variable $places := collection($path-to-syriaca-data||"data/places/tei/");
declare variable $persons := collection($path-to-syriaca-data||"data/persons/tei/");

(:
NOTE: headwordPath is relative to the body element.
TBD: Documentation
:)
declare variable $entity-config := map {
  "person": {
    "headwordPath": "listPerson/*/persName",
    "collection": $persons
  },
  "place": {
    "headwordPath": "listPlace/place/placeName",
    "collection": $places
  },
  "work": {
    "headwordPath": "bibl/title",
    "collection": $works
  }
};

(: This is used for grouping variant language tags into their main buckets :)
declare variable $lang-tag-groups := map {
  "en": ("en", "en-x-gedsh"),
  "syr": ("syr", "syr-Syrj")
};

let $records :=
  for $entity in map:keys($entity-config)
  for $doc in $entity-config?$entity?collection
  let $uri := $doc/TEI/teiHeader/fileDesc/publicationStmt/idno[@type="URI"]/text()
    => substring-before("/tei")
  
  let $labels := functx:dynamic-path($doc//body, $entity-config?$entity?headwordPath)
  let $headwords := $labels[contains(@srophe:tags, "syriaca-headword")]
  let $headwordColumns :=
    for $h in $headwords
    let $langTag := $h/@xml:lang/string()
    let $grpedTag := 
      for $grp in map:keys($lang-tag-groups)
      return if(functx:is-value-in-sequence($langTag, $lang-tag-groups?$grp)) then $grp else ()
    let $langTag := if($grpedTag) then $grpedTag else $langTag
    return element {$langTag||"_headword"} {local:clean-descendant-text($h)}
  return element {"row"} {
    element {"uri"} {$uri},
    element {"entity_type"} {$entity},
    $headwordColumns
  }
 
(: Add empty fields to ensure they get converted to CSV columns properly :)
let $columnNames := $records/*/name() => distinct-values()
let $rows := 
  for $r in $records
  return element {$r/name()} {
    $r/*,
    for $c in $columnNames where not($r/*[name() = $c]) return element {$c} {}
  }

return element {"csv"} {$rows} => csv:serialize({"header": "yes"})