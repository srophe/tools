xquery version "3.1";

(:
: Module Name: Record Title from Headwords
: Module Version: 1.0
: Copyright: GNU General Public License v3.0
: Proprietary XQuery Extensions Used: None
: XQuery Specification: 08 April 2014
: Module Overview: This main module updates the Syriaca.org record titles
:                  (/TEI/titleStmt/title) based on the English and Syriac
:                  language headwords. It should be run periodically to
:                  ensure these data remain synced.
:)

(:~ 
: This main module runs against all Syriaca entities except CBSS records.
: It utilizes XQuery update functionalities to directly change the TEI XML
: records.
:
: @author William L. Potter
: @version 1.0
:)

import module namespace functx="http://www.functx.com";

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

for $entity in $entity-config?*
for $doc in $entity?collection
let $labels := functx:dynamic-path($doc//body, $entity?headwordPath)
let $headwords := $labels[contains(@srophe:tags, "syriaca-headword")]

(: If the record is an anonymous record, grab only the English-language anonymous description :)
(: Note: Some records have extraneous anonymous descriptions, so don't want to include them :)
let $anonymousDesc := if($labels/../@ana/string() => contains("syriaca-anonymous"))
  then " — "||$labels[contains(@srophe:tags, "anonymous-description")][starts-with(@xml:lang, "en")] => local:clean-descendant-text()
  else ()


let $enHeadword := local:clean-descendant-text($headwords[starts-with(@xml:lang, "en")])
let $syrHeadword := local:clean-descendant-text($headwords[starts-with(@xml:lang, "syr")])
let $normalizedRecordTitle := 
    element {"title"} {
      attribute {"level"} {"a"},
      attribute {"xml:lang"} {"en"},
      try {
      if($syrHeadword != "") then (
        $enHeadword||$anonymousDesc||" — ",
        element {"foreign"} {
          attribute {"xml:lang"} {"syr"},
          $syrHeadword
        }
      )
      else $enHeadword||$anonymousDesc
    }catch * {
    document-uri($doc)
  }
 }
 return replace node $doc//titleStmt/title with $normalizedRecordTitle