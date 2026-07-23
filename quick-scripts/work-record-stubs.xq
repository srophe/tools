xquery version "3.1";

import module namespace functx="http://www.functx.com";
import module namespace template="http://wlpotter.github.io/ns/template" at "/home/arren/Documents/GitHub/csv-to-srophe/modules/template.xqm";

declare default element namespace "http://www.tei-c.org/ns/1.0";
declare namespace srophe="https://srophe.app";

declare variable $path-to-csv := "/home/arren/Downloads/Work URIs for Translation Corpus - Comprehensive.csv";
declare variable $csv := csv:doc($path-to-csv, map {"header": "yes"});

declare variable $path-to-syriaca-data := "/home/arren/Documents/GitHub/syriaca-data/";
declare variable $persons := collection($path-to-syriaca-data||"data/persons/tei/");

declare variable $path-to-template := "/home/arren/Documents/GitHub/tools/quick-scripts/works-template.xml";
declare variable $template := doc($path-to-template);

declare variable $work-uri-base := "http://syriaca.org/work/";

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

for $row in $csv/*:csv/*:record
where not($row/*:work_URI/text() = "Needed") and $row/*:work_URI/text() => normalize-space() != ""

let $title := $row/*:Title/text()
let $uri := $row/*:work_URI/text()
let $workID := $uri => substring-after($work-uri-base)
let $authorURI := $row/*:Author_URI/text()
let $authorName := $row/*:Author_name/text()
let $authorIsPseudo := $row/*:Pseudo != ""
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
      attribute {"resp"} {"http://syriaca.org"},
      $title
    },
    (: AUTHOR, if there is one :)
    if($authorURI != "") then
      element {"author"} {
        attribute {"ref"} {$authorURI},
        if($authorIsPseudo) then
          attribute {"ana"} {"pseudo"}
        else (),
        (: TODO: RESP OR SOURCE? :)
        attribute {"xml:lang"} {"en"},
        (: RECORD TITLE FROM SBD :)
        $personIndex?$authorURI/text()[1],
        if($personIndex?$authorURI/foreign) then 
        element {"foreign"} {
          $personIndex?$authorURI/foreign/@*,
          $personIndex?$authorURI/foreign/text()
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
    }, (: TODO: ask Dan if crediting him and/or student as creator - can also be done in the template file :)
    element {"respStmt"} {
      element {"resp"} {
        (: TODO ask Dan what this should be, if anything  - can also be done in the template file :)
        element {"name"} {
          attribute {"type"} {"person"},
          attribute {"ref"} {"http://syriaca.org/documentation/editors.xml#"}
          (: TODO ask Dan if should be anyone specific, or if leave to be filled in :)
        }
      }
    }
  },
  element {"revisionDesc"} {
    attribute {"status"} {"draft"},
    element {"change"} {
      attribute {"who"} {"http://syriaca.org/documentation/editors.xml#"},
      attribute {"when"} {}
      (: TODO: ask Dan if we want a specific change for the stub or if we should leave blank for them to fill in :)
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
TODO: File I/O and send Dan some samples to review
:)

return try {
  template:merge-record-into-template($stub, $template, $uri)
} catch * {
  $row
}

