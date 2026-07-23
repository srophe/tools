xquery version "3.1";

import module namespace functx="http://www.functx.com";

declare default element namespace "http://www.tei-c.org/ns/1.0";
declare namespace srophe="https://srophe.app";
declare namespace output = 'http://www.w3.org/2010/xslt-xquery-serialization';

declare option output:omit-xml-declaration 'no';
declare option output:indent 'yes';

declare variable $path-to-csv external;
declare variable $csv := csv:doc($path-to-csv, map {"header": "yes"});

declare variable $path-to-syriaca-data external;
declare variable $persons := collection($path-to-syriaca-data||"data/persons/tei/");

declare variable $path-to-template external;
declare variable $template := doc($path-to-template);

declare variable $output-directory external;

declare variable $work-uri-base := "http://syriaca.org/work/";
declare variable $multi-author-delimiter external := "\|";

declare variable $listBibl-type-configs := map {
  "editions": {
    "head-text": "Editions",
    "desc-text": "editions",
    "include-cbss-in-desc": true(),
    "bibl-type": "lawd:Edition",
    "requires-textLang": false()
  },
  "modernTranslations": {
    "head-text": "Modern Translations",
    "desc-text": "modern translations",
    "include-cbss-in-desc": true(),
    "bibl-type": "syriaca:ModernTranslation",
    "requires-textLang": true()
  }
};

(: Create a map of author URI to record title :)
declare variable $personIndex := map:merge(
  for $person in $persons
  let $uri := $person/TEI/text/body/listPerson/*/idno[@type="URI"][1]/text()
  let $title := $person/TEI/teiHeader/fileDesc/titleStmt/title
  return map {$uri: $title}
);

declare variable $cbss-index := map:merge (
  for $filename in file:list($path-to-syriaca-data||"data/bibl/json/")
  let $uri := "http://syriaca.org/cbss/"||$filename => substring-before(".json")
  let $json := json:doc($path-to-syriaca-data||"data/bibl/json/"||$filename, map {"format": "xquery"})
  let $title := $json?data?title
  let $lang := $json?data?language
  return map {
    $uri: {
      "title": $title,
      "lang": $lang
    }
  });


declare function local:create-list-bibl($bibl_uri as xs:string, $type as xs:string, $work_id as xs:string, $textLang as xs:string?)
as node() {
  element {"listBibl"} {
      attribute {"type"} {$type},
      element {"head"} {$listBibl-type-configs?$type?head-text},
      element {"desc"} {
        attribute {"xml:lang"} {"en"},
        "This is not a comprehensive list of "||$listBibl-type-configs?$type?desc-text||" related to this work.",
        if($listBibl-type-configs?$type?include-cbss-in-desc) then 
          ("Further citations may be available through ",
           element {"ref"} {
             attribute {"target"} {"http://syriaca.org/cbss"},
             "The Comprehensive Bibliography on Syriac Studies"
           },
           "."
         )
      },
      element {"bibl"} {
        attribute {"xml:id"} {"bib"||$work_id||"-1"},
        attribute {"type"} {$listBibl-type-configs?$type?bibl-type},
        element {"title"} {
          attribute {"xml:lang"} {$cbss-index?$bibl_uri?lang},
          $cbss-index?$bibl_uri?title
        },
        element {"ptr"} {
          attribute {"target"} {$bibl_uri}
        },
        if($listBibl-type-configs?$type?requires-textLang) then
          element {"textLang"} {
            attribute {"mainLang"} {$textLang}
          }
        else ()
      }
    }
};

(:~
: Copied and customized from https://github.com/wlpotter/csv-to-srophe template module. 
: @param $recordUri is the full URI of the document, including the URI-base, e.g. "http://syriaca.org/place/78".
: Although this URI is included in a tei:idno element within the $record, its location is not reliable entity-type
: to entity-type. Thus, rather than risking an inaccurate XPath, this value is passed to the function. :)
declare function local:merge-record-into-template($record as node(),
                                                     $template as node(),
                                                     $recordUri as xs:string,
                                                     $active-namespaces as item()*)
as node()
{
  (: merge titleStmt from record into template :)
  let $headwords := $record//*[@srophe:tags="#syriaca-headword"]
  let $recordTitle := local:create-record-title-from-headwords($headwords, "en")
  let $titleStmt := 
  <titleStmt>
    {
      $recordTitle,
      $template//titleStmt/*[not(name() = "respStmt")],
      $record//titleStmt/editor[@role="creator"],
      $record//titleStmt/respStmt,
      $template//titleStmt/respStmt
    }
  </titleStmt>
  
  (: editionStmt comes from the template :)
  let $editionStmt := $template//editionStmt
  
  (: build publicationStmt based on record's URI :)
  (: as the document's idno may change depending on its entity, this value is passed to the function :)
  let $pubStmtIdno := <idno type="URI">{$recordUri || "/tei"}</idno>
  let $publicationStmt := (: careful here as there could be variance in the publicationStmt. I don't think there is but might need to revisit this. :)
  <publicationStmt>
    {
      $template//publicationStmt/authority,
      $pubStmtIdno,
      $template//publicationStmt/availability,
      <date>{fn:current-date()}</date>
    }
  </publicationStmt>
  
  (: build the seriesStmt from tepmlate :)
  let $seriesStmt := $template//seriesStmt
  
  (: build sourceDesc from template :)
  let $sourceDesc := $template//sourceDesc
  
  (: build fileDesc from component parts :)
  let $fileDesc :=
  <fileDesc>
    {
      $titleStmt,
      $editionStmt,
      $publicationStmt,
      $seriesStmt,
      $sourceDesc
    }
  </fileDesc>
  
  (: build the encodingDesc which comes from the template :)
  let $encodingDesc := $template//encodingDesc
  
  (: build the profileDesc which comes from the template :)
  let $profileDesc := $template//profileDesc
  
  (: build the revisionDesc which comes from the record :)
  (: NOTE: potentially add a revisionDesc change for template merging? :)
  let $revisionDesc := $record//revisionDesc
  
  (: build teiHeader from component parts :)
  let $teiHeader := 
  <teiHeader>
  {
    $fileDesc,
    $encodingDesc,
    $profileDesc,
    $revisionDesc
  }
  </teiHeader>

  (: the text node comes entirely from the $record :)
  let $text := $record//text
  
  (: Add the @corresp attributes to the record's abstract(s) :)
  let $seriesStmtIdnos := $seriesStmt/idno/text() => string-join(" ")
  let $text := local:add-corresp-to-abstract($text, $seriesStmtIdnos)
  
  (: now the TEI node can be constructed; the xml:lang attribute comes from the record :)
  let $baseLanguage := string($record/TEI/@xml:lang)
  let $teiNode :=
  element {QName("http://www.tei-c.org/ns/1.0", "TEI")} {$active-namespaces, attribute {"xml:lang"} {"en"}, $teiHeader, $text}
  
  (: build list of processing instructions based on template. This should be the various schema associations and any other CSS, etc. associations :)
  let $processingInstructions := $template/processing-instruction()
  return document {$processingInstructions, $teiNode}
};

(:~ 
: takes input of some sequence of headword elements.
: returns a tei:title element of the form:
: <title level="a" xml:lang="{$baseLanguage}">Base-Language Headword - <foreign xml:lang="{non-base-language}">Non-Base-Language-Headword</foreign></title> 
: 
:)
declare function local:create-record-title-from-headwords($headwords as element()+,
                                                             $baseLanguage as xs:string)
as element()
{
  let $baseLanguageHeadwords := $headwords[@xml:lang = $baseLanguage]
  let $foreignHeadwords := $headwords[@xml:lang != $baseLanguage]
  return 
  <title level="a" xml:lang="{$baseLanguage}">
    {
      fn:string-join($baseLanguageHeadwords/text(), " - ") (: combine all base-language headword's text nodes, separated by " - ":),
      for $headword at $i in $foreignHeadwords
        let $joiner := if($i > 1) then " - " else "- " (: avoid adding an extra space between base and foreign headwords:)
        return ($joiner, <foreign xml:lang="{string($headword/@xml:lang)}">{$headword/text()}</foreign>)
    }
  </title>
  
};

declare function local:add-corresp-to-abstract($textElement as node(), $seriesStmtIdnos as xs:string)
as node()
{
  (: should be text, body, listEl, El, :)
  let $body := $textElement/body
  let $listEl := $body/* (: the one ensures we don't pick up the listRelation element :)
  let $entity := if(contains($listEl/name(), "list")) then $listEl/*[1] (: for places and persons, listRelation is listEl/*[2] :)else $listEl (: for subjects, the 'listEl' is actually entryFree :)
  let $entitySiblings := $listEl/*[2] (: listRelation for persons and places :)
  let $entity :=
    element {$entity/name()} {$entity/@*,
    for $ch in $entity/*
    return if($ch/@type="abstract") then 
       element {$ch/name()} {$ch/@*, attribute {"corresp"} {$seriesStmtIdnos}, $ch/*}
    else $ch
  }
  let $listEl := 
    if(contains($listEl/name(), "list")) then 
      element {$listEl/name()} {$listEl/@*, $entity, $entitySiblings}
    else $entity (: for subjects, the 'listEl' is actually entryFree :)
  let $body := element {$body/name()} {$body/@*, $listEl, $body/*[2]}
  let $text := element {$textElement/name()} {$textElement/@*, $body}
  return $text
};

(: Creates the output directory path, if it does not yet exist :)
let $nothing := file:create-dir($output-directory)

(: Run through the CSV and create the stub records :)
for $row in $csv/*:csv/*:record
where not($row/*:work_URI/text() = "Needed") and $row/*:work_URI/text() => normalize-space() != ""

let $title := $row/*:Title/text()
let $uri := $row/*:work_URI/text()
let $workID := $uri => substring-after($work-uri-base)
let $authorURI := $row/*:Author_URI/text() => tokenize($multi-author-delimiter)
let $authorName := $row/*:Author_name/text()
let $authorIsPseudo := for $a in tokenize($row/*:Pseudo, $multi-author-delimiter) return $a != ""
let $cbssURITranslation := $row/*:CBSS_URI__of_the_actual_source_of_the_transcription_/text()

let $translationListBibl := 
  if(starts-with($cbssURITranslation, "http://syriaca.org/cbss/")) then 
    local:create-list-bibl($cbssURITranslation, "modernTranslations", $workID, "en")
  else ()

let $work_bibl :=
  element {"bibl"} {
    (: BIBL ATTRIBUTES :)
    attribute {"xml:id"} {"work-"||$workID},
    attribute {"type"} {"lawd:ConceptualWork"},
    (: TITLE :)
    element {"title"} {
      attribute {"xml:id"} {"name"||$workID||"-1"},
      attribute {"xml:lang"} {"en"},
      attribute {"srophe:tags"} {"#syriaca-headword"},
      attribute {"resp"} {"http://syriaca.org"}, (: SOURCE to the translation bibl :)
      $title
    },
    (: AUTHOR, if there is one :)
    if($authorURI != "") then
      for $author at $i in $authorURI
      return element {"author"} {
        attribute {"ref"} {$author},
        if($authorIsPseudo[$i]) then
          attribute {"ana"} {"pseudo"}
        else (),
        attribute {"source"} {"#bib"||$workID||"-1"},
        attribute {"xml:lang"} {"en"},
        (: RECORD TITLE FROM SBD :)
        $personIndex?$author/text()[1],
        if($personIndex?$author/foreign) then 
        element {"foreign"} {
          $personIndex?$author/foreign/@*,
          $personIndex?$author/foreign/text()
        }
        else ()
      }
    else (),
    (: IDNO :)
    element {"idno"} {
      attribute {"type"} {"URI"},
      $uri
    },
    (: LIST BIBL, cf. local:create-list-bibl() :)
    $translationListBibl
  }

let $text := element {"text"} {
  element {"body"} {
    $work_bibl
  }
}

let $stubHeader := element {"teiHeader"} {
  element {"titleStmt"} {
    element {"editor"} {
      attribute {"role"} {"creator"},
      attribute {"ref"} {"http://syriaca.org/documentation/editors.xml#"}
    }, (: TODO: credit Dan's student :)
    (: TODO: Retain a stub editor for the reviewers :)
    element {"respStmt"} { (: TODO: create a stub respStmt for the reviewers, maybe with a comment to fill in :)
      element {"resp"} {
        (: TODO credit Dan's student :)
        element {"name"} {
          attribute {"type"} {"person"},
          attribute {"ref"} {"http://syriaca.org/documentation/editors.xml#"}
          (: TODO credit the student:)
        }
      }
    }
  },
  element {"revisionDesc"} {
    attribute {"status"} {"draft"},
    element {"change"} {
      attribute {"who"} {"http://syriaca.org/documentation/editors.xml#"},
      attribute {"when"} {}(: TODO: Fill in for the created stub change, but leave blank for the review editors one :)
      (: TODO: add a CREATED: stub record... and a stub change for the review editors :)
    }
  }
}
let $stub := element {"TEI"} {
  attribute {"xml:lang"} {"en"},
  $stubHeader,
  $text
}
(:
TODO: Review questions with Dan
:)

let $namespaces :=
(
  namespace {"srophe"} {"https://srophe.app"},
  namespace {"syriaca"} {"http://syriaca.org"}
)
let $filepath := $output-directory||$workID||".xml"
return file:write(
  $filepath,
  local:merge-record-into-template($stub, $template, $uri, $namespaces),
  map {
    "indent": "yes",
    "omit-xml-declaration": "no"
  })