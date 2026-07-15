xquery version "3.1";

(:
: Module Name: Record Title from Headwords
: Module Version: 1.0
: Copyright: GNU General Public License v3.0
: Proprietary XQuery Extensions Used: None
: XQuery Specification: 08 April 2014
: Module Overview: This main module updates the contents of Syriaca.org
:                  work records (New Handbook of Syriac Literature) to
:                  ensure that the creators (author and editor elements)
:                  use the record title from the referenced person record
:                  in the Syriac Biographical Dictionary. It should be run 
:                  periodically to ensure these data remain synced.
:)

(:~ 
: This main module runs against Syriaca work entities.
: It utilizes XQuery update functionalities to directly change the TEI XML
: records.
:
: @author William L. Potter
: @version 1.0
:)

import module namespace functx="http://www.functx.com";

declare default element namespace "http://www.tei-c.org/ns/1.0";
declare namespace output = 'http://www.w3.org/2010/xslt-xquery-serialization';

declare option output:omit-xml-declaration 'no';
declare option output:indent 'yes';

declare variable $path-to-repo := "/home/arren/Documents/GitHub/syriaca-data/"; (: TODO: Change to external, pass via Python wrapper :)
declare variable $works := collection($path-to-repo||"data/works/tei/");
declare variable $places := collection($path-to-repo||"data/places/tei/");
declare variable $persons := collection($path-to-repo||"data/persons/tei/");

(: Create a map of author URI to record title :)
let $personIndex := map:merge(
  for $person in $persons
  let $uri := $person/TEI/text/body/listPerson/*/idno[@type="URI"][1]/text()
  let $title := $person/TEI/teiHeader/fileDesc/titleStmt/title
  return map {$uri: $title}
)
for $doc in $works
where $doc//body/bibl/author or $doc//body/bibl/editor
for $creator in $doc//body/bibl/*[name() = "author" or name() = "editor"] (: include both authors and editors :)
let $creatorUri := $creator/@ref/string()
let $updatedCreator := 
  if($creatorUri != "") then 
    element {$creator/name()} {
      $creator/@ref,
      $creator/@source,
      $creator/@resp,
      $creator/@role,
      attribute {"xml:lang"} {"en"},
      $personIndex?$creatorUri/node() (: Look up the title in the author index and get the child text and element nodes :)
    }
  else $creator (: if there is no URI, then keep the author element as-is so we don't lose any data :)
return replace node $creator with $updatedCreator
