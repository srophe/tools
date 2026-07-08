# Syriaca-data TEI schema reference

All records are TEI XML with default namespace `http://www.tei-c.org/ns/1.0`
(prefix `tei` below) and a custom `srophe` namespace `https://srophe.app` used
for a few editorial attributes (`srophe:tags`, `srophe:computed-start/end`).
Register both when writing XPath with `lxml`:

```python
NS = {"tei": "http://www.tei-c.org/ns/1.0", "srophe": "https://srophe.app"}
```

A handful of files (a few dozen out of ~9,500) have minor id-uniqueness quirks
that trip up strict XML validation (e.g. a duplicated `xml:id`). Parse with
`etree.XMLParser(recover=True)` so these don't abort a corpus-wide scan.

This reference is drawn from two sources: direct inspection of the TEI data in
[`srophe/syriaca-data`](https://github.com/srophe/syriaca-data), and the
project's own editorial/schema documentation in
[`srophe/Gaddel/documentation`](https://github.com/srophe/Gaddel/tree/main/documentation)
— specifically `syriaca-tei-main.odd` (the TEI customization, i.e. the
ground-truth schema), `confessions.xml`, `place-types.xml`, `syriaca-tags.xml`,
`work-subject-classifications.xml`, `relations.html`, `dates.html`, and
`uris.html`. (The Gaddel repo's own top-level README calls itself deprecated
as of 2014 and points elsewhere, but the individual `documentation/` files are
current and are cross-linked from syriaca.org's live documentation menu — the
README note appears to be stale boilerplate from a rename, not an active
deprecation. Worth a sanity check against the live site if something here ever
looks wrong.)

## Places — `data/places/tei/{id}.xml`

```
TEI/text/body/listPlace/place[@type]
```

- `@type`: a closed vocabulary of 25 values, each with an official definition
  (see table below).
- `placeName[@xml:lang]`: one per name variant. The headword (preferred
  display name) has `srophe:tags="#syriaca-headword"`.
- `desc[@type='abstract']`: the summary description (English prose).
- `location[@type='gps'][@subtype='preferred'|'alternate']/geo`: text content
  is `"<lat> <long>"` space-separated.
- `location[@type='relative']`: prose description when no coordinates exist.
- `event[@when|@notBefore|@notAfter]/desc`: historical events tied to the place.
- `state[@type='existence'][@from][@to]`: the span during which the place (as
  that type) existed/was in use. Natural features often have no `@to`.
- `state[@type='confession'][@ref][@from][@to]/desc`: attested religious
  communities present at the place, each `@ref` pointing into the confessions
  taxonomy (see "Religious communities (confessions)" below).
- `idno[@type='URI']`: one is the canonical `http://syriaca.org/place/{id}`;
  others may be Pleiades, Wikipedia, or (deprecated/redirect) links — see "URI
  policy" below.
- `listRelation/relation[@type][@ref][@active][@passive]` (directed) or
  `[@mutual]` (space-separated pair of URIs, symmetric): see "Relations"
  below for the full vocabulary of `@name` values, not just `@type`.

### Place types (`place/@type`) — full vocabulary

The place-type vocabulary has 25 values. Earlier versions of this doc listed
only 20 — `cemetery`, `composite`, `madrasa`, and `valley` were missing.
Definitions are from `documentation/place-types.xml` (the project's own
taxonomy document):

| Type | Definition |
|---|---|
| `building` | A construction for which there is no narrower category, such as a church or mosque (e.g. palaces, named city gates). |
| `cemetery` | A space designated for interment or final disposition of the deceased. |
| `church` | A building for Christian religious services — parish, monastic, cathedral, or small chapel — but not a chapel that is part of a larger church. |
| `composite` | A named place concept merging multiple distinct place types (e.g. a city and a diocese). More specific types are preferred when possible. |
| `designated-space` | An area with artificial boundaries, not necessarily built up (e.g. a town square, polo ground), with no narrower category. |
| `diocese` | An ecclesiastical province governed by a bishop, archbishop, or metropolitan. |
| `fortification` | A military outpost such as a fort or castle. |
| `island` | A land-mass smaller than a continent, surrounded on all sides by water. |
| `madrasa` | A building or space for instruction in the Islamic sciences. |
| `monastery` | A whole monastic complex: living quarters, church(es), and potentially refectory/library/school. |
| `mosque` | A building or designated space for Muslim congregational prayers; may be part of a larger complex. |
| `mountain` | An elevated physical feature, from Mt. Ararat down to a prominent hill. |
| `natural-feature` | A natural feature with no narrower category (e.g. forests, hot springs). |
| `open-water` | Seas, lakes, oceans, ponds. |
| `parish` | An ecclesiastical region below a diocese, presided over by a priest. |
| `province` | A political unit subject to a "state" but larger than a city (covers multiple historical administrative levels, e.g. Ottoman vilayet/sanjak/kaza/nahiye). |
| `quarter` | A subdivision of an urban center. |
| `region` | A geographic extent larger than a city without a corresponding politico-administrative apparatus — a small valley up to a whole continent. |
| `river` | A stream of any size, including wadis even when not filled with water year-round. |
| `settlement` | Any collection of civilian residences, village to metropolis. |
| `state` | A sovereign government: empire, kingdom, caliphate, independent emirate. |
| `synagogue` | A building for Jewish worship. |
| `temple` | A building for pagan worship. |
| `unknown` | A place whose name is known but whose type is not. |
| `valley` | A depression longer than it is wide, typically between hills/mountains with a river or wadi running through it. |

## Persons — `data/persons/tei/{id}.xml`

```
TEI/text/body/listPerson/person[@ana]
```

- `@ana`: space-separated tags like `#syriaca-author #syriaca-saint`.
- `persName[@xml:lang]`, headword same convention as places.
- `note[@type='abstract']`: summary description; may have `@corresp` listing
  which sub-publications (gazetteer, saints, authors...) it belongs to.
- `floruit/date[@notBefore][@notAfter][@when]`, `birth/date`, `death/date`:
  `birth` and `death` may also carry a nested `placeName[@ref]`. See "Date
  encoding conventions" below for how prose dates like "early 8th century"
  map to these numeric attributes.
- `gender[@ana]`: free text with a taxonomy ref.
- `state[@type='status'|'occupation'|'religious-affiliation'][@ref]/desc`:
  status (e.g. saint), occupation (e.g. bishop, monastic head), and religious
  affiliation are each modeled as a `state`, not a dedicated element — this is
  the field to filter on for "all bishops" or "all Syrian Orthodox" queries.
- `event[@type='veneration'][@when]`: liturgical commemoration dates (note:
  `@when` here is often a `--MM-DD` recurring-date, not a year).
- `relation[@type]`: disambiguation, place (person-to-place link), or (rare)
  pseudonymity — see "Relations" below for the actual `@name` vocabulary.

## Works — `data/works/tei/{id}.xml`

```
TEI/text/body/listBibl/bibl[@xml:id^="work-"]
```

Note the root element is `bibl`, not a dedicated `work` tag.

- `title[@xml:lang]`: name variants, same headword convention.
- `author[@ref]`: URI of the person record, with inline `persName` for display.
- `@subtype`: per the schema, `bibl`/work-record `@subtype` is one of
  `original-composition`, `revision`, or `translation` — useful for
  distinguishing an original work from a later revision or translation of it.
- `note[@type=...]`: see "note/@type vocabulary" below — the closed list
  includes `incipit`, `explicit`, `prologue`, `filiation`, `content`,
  `scope`, and `misc`, each possibly containing nested `bibl` citation
  elements. (Earlier documentation for this skill described types like
  `editions`, `MSS`, and `modernTranslation`, which are **not** in the
  current closed vocabulary in `syriaca-tei-main.odd` — those may reflect an
  older convention or records predating a schema tightening. If you hit a
  `note` with an unexpected `@type` while querying, trust what's actually in
  the file over this document.)
- `idno[@type=...]`: canonical `URI` plus catalog-specific ids — the closed
  vocabulary is `URI`, `ISBN`, `ISSN`, `DOI`, `FIEY` (Fiey's *Assyrie
  chrétienne*), `BHS` (Bibliotheca Hagiographica Syriaca), `BHO`
  (Bibliotheca Hagiographica Orientalis), and `CPG` (Clavis Patrum
  Graecorum).
- Subject classification: works may be tagged against the "Preliminary
  Subject Classifications" taxonomy — see "Work subject classifications"
  below. (This skill has not yet verified the exact element/attribute used
  to attach a subject to a work record; treat the taxonomy as a reference
  vocabulary for now rather than assuming a specific XPath.)

## SPEAR factoids — `data/spear/tei/{id}.xml`

```
TEI/text/body/ab[@type='factoid'][@subtype]
```

SPEAR (Syriac Persons, Events, and Relations) breaks biography into discrete,
individually-sourced claims rather than one prose entry. Each factoid:

- `@subtype`: nameVariant, gender, occupation, sanctity, religious-affiliation,
  and others — an open-ended but small vocabulary.
- `listPerson/person/persName[@ref]`: the subject (URI ref, often with no text
  — the descriptive text usually lives inside the specific claim element below
  instead, e.g. `trait`, `occupation`, `event`, each with a `note[@type='desc']`
  containing prose that itself contains another `persName[@ref]` pointing to
  the same person — expect two `persName` hits per factoid, one bare and one
  with text).
- `bibl[@type='primary']/ptr[@target]` + `citedRange`: the source(s) for the
  claim — usually a `work/` URI plus a `bibl/` (bibliography entry) URI.
  `citedRange` may specify a unit — the schema's `unit` vocabulary is `pp`,
  `ff`, `part`, `chapter`, `stanza`, `verse`, `paragraph`, `section`, `word`,
  `character`.

## Relations — `relation[@name][@type][@active][@passive|@mutual][@source]`

Relations appear inline (`person/relation`, `place/relation`) or in a
`listRelation` block, and connect any two (or more) Syriaca.org entities.
This section supersedes the older, incomplete note that only `type`s like
`contained-within`, `disambiguation`, and `see-also` exist — those are
`@type` values (a broad category used for display), not the specific
relationship, which lives in `@name`.

**Attributes** (per `documentation/relations.html`):

| Attribute | Meaning | Contains |
|---|---|---|
| `@name` | the specific relationship | an RDF relationship class name, e.g. `syriaca:born-at` or `snap:DaughterOf` |
| `@type` | broad category, used for display grouping | e.g. `disambiguation` |
| `@active` | the "doer" in a non-mutual relation | URI (or local pointer) of the active entity |
| `@passive` | the "target" in a non-mutual relation | URI (or local pointer) of the passive entity |
| `@mutual` | all participants in a symmetric relation | space-separated URIs |
| `@source` | citation supporting the relation | URI of the `bibl/` or `manuscript/` record (not `work/`) |

**`@name` vocabulary actually documented** (non-exhaustive — the project also
draws on the [SNAP ontology](http://snapdrgn.net/ontology) with a `snap:`
prefix for prosopographical relations like `snap:DaughterOf`):

| `@name` | Entities | Meaning |
|---|---|---|
| `syriaca:born-at` | person (active) → place (passive) | Person was born at place. |
| `syriaca:died-at` | person (active) → place (passive) | Person died at place. |
| `syriaca:commemorated` | work (active) → person (passive) | Work commemorates person. |
| `syriaca:has-literary-connection-to-place` | person → place | Person has a literary connection to place. |
| `syriaca:has-relation-to-place` | person → place | Unspecified connection between person and place. |
| `syriaca:different-from` | entities of the same type (mutual) | Entities are not identical but could be confused (disambiguation). |
| `syriaca:possibly-identical` | persons (mutual) | Two person records may describe the same individual (disambiguation). |
| `syriaca:share-a-name` | places (mutual) | Places share a name (disambiguation). |
| `syriaca:share-a-title` | works (mutual) | Works share a title (disambiguation). |
| (place hierarchy) `contained-within` | place → place | Used as `@type`/taxonomy `@ref` (`.../taxonomy/broader`) rather than a `syriaca:` `@name` — place-hierarchy edges from `listRelation`. |

When filtering relations, prefer matching on `@name` if you know the specific
relationship you want (e.g. "everyone born at Edessa" → `@name` =
`syriaca:born-at`); fall back to `@type` for broad categories like
disambiguation.

## Religious communities (confessions) — `state[@type='confession'|'religious-affiliation']/@ref`

The confessions vocabulary (`documentation/confessions.xml`) is a nested
tree, not a flat list. Top-level groups are **Christians, Gnostics, Jews,
Muslims, Yezidis, Zoroastrians** — Gnostics/Jews/Muslims/Yezidis/Zoroastrians
are siblings of Christians, not sub-groups of it. Under Christians:

- **Syriac** → Bardaisanites; **East Syrian** (Ancient Church of the East,
  Assyrian Evangelical Church, Chaldean Catholic, Church of the East);
  **Indian** (Chaldean Syrian Church, Malabar Catholic Church, Malabar
  Independent Syrian Church, Malankara Catholic Church, Malankara Orthodox
  Syrian Church, Malankara Syriac Orthodox Church, Mar Thoma Syrian Church);
  **West Syrian** (Maronite, Melkite, Syrian Catholic, Syrian Orthodox)
- **Arabic** → Arabic Protestant, Rum Orthodox
- **Armenian** → Armenian Catholic, Armenian Chalcedonian, Armenian
  Orthodox, Armenian Protestant
- **Coptic**, **Ethiopic**, **Georgian** (no sub-groups)
- **Greek** → Greek Catholic, Greek Orthodox, Marcionites
- **Latin** → Protestant, Roman Catholic

Other top-level groups: **Gnostics** → Mandaeans, Manichaeans; **Jews** →
Karaite, Rabbanite; **Muslims** → Khariji, Shiʿa (→ Ismaʿili, Twelver,
Zaydi), Sunni; **Yezidis**; **Zoroastrians**.

`@ref` values are the taxonomy `xml:id`s, lowercase-hyphenated (e.g.
`syrian-orthodox`, `church-of-the-east`, `rabbanite`). The project's own
caveat is worth repeating: these labels are scholarly convention for the
project's purposes, not a claim about self-identification, uniformity, or
mutual exclusivity.

## Work subject classifications

A separate, preliminary genre/subject taxonomy for works
(`documentation/work-subject-classifications.xml`), adapted from Wright,
Duval, and Brock's standard reference works on Syriac literature:

Bible (Single Biblical Book, Collected Biblical Books, Lectionary, Psalter) ·
Theology/Biblical Interpretation (Bible Commentary, Poem with Biblical
Motif, Bible Vocalization/Masora, Scholion, Question and Answer, Other) ·
Liturgy (Missal, Daily Office, Ecclesiastical Office, Collection of Choral
Services/Homilies/Hymns, Prayer(s), Services for Life Events) · Spiritual or
Ascetic Disciplines · Hagiography (Martyr Acts, Life/Lives of Saints or
Ascetics, Poem(s) on Saints or Ascetics, Other) · Apologetics or
Heresiology · Law or Ecclesiastical Governance (Council Account/Record,
Canon Law, Civil Law) · History (Universal, Particular) · Philosophy (Logic,
Ethics) · Linguistics (Grammar, Lexicon, Rhetoric/Poetics) · Natural or
Therapeutic Science (Medicine, Agriculture, Chemistry,
Astronomy/Cosmography/Geography) · Mathematics · Natural History · Popular
Narratives.

The classification is hierarchical: a work gets the most specific label that
applies, falling back to the parent category otherwise. As noted above, this
skill hasn't yet confirmed the exact XPath used to attach a subject label to
a work record — treat this as reference vocabulary.

## `xml:lang` — closed value list

`syriaca-tei-main.odd` closes the `xml:lang` attribute to a specific set of
values (useful for the `--lang` search flag): `ar` (Arabic), `ar-Syrc`,
`ar-Syre`, `ar-Syrj`, `ar-Syrn` (Arabic written in Syriac/Estrangela/Serto/
East-Syriac script — i.e. Garshuni, by script variant), `cop` (Coptic), `cu`
(Church Slavonic), `de` (German), `de-x-baumstrk` (German, Baumstark's
classification conventions), `el` (Modern Greek), `en` (English),
`en-x-gedsh`, `en-x-lah`, `en-x-srp1` (English, per specific reference-work
citation conventions — GEDSH, etc.), `es` (Spanish), `fr` (French),
`fr-x-bhs`, `fr-x-fiey` (French, per BHS/Fiey citation conventions), `gez`
(Geʿez/Classical Ethiopic), `grc` (Ancient Greek), `hy` (Armenian), `it`
(Italian), `ka` (Georgian), `la` (Latin), `mal` (Malayalam), `mal-Syrc`,
`mal-Syre`, `mal-Syrj`, `mal-Syrn` (Malayalam in Syriac script variants —
i.e. Garshuni), `nl` (Dutch), `pt` (Portuguese), `ru` (Russian), `syr`
(Syriac), `syr-Syre`, `syr-Syrj`, `syr-Syrn` (Syriac in Estrangela/Serto/
East-Syriac script specifically), `syr-x-syrm` (Syriac, specific
convention), `sog` (Sogdian), `tr` (Turkish).

## `note/@type` vocabulary

Closed list per `syriaca-tei-main.odd`: `initial-rubric`, `final-rubric`,
`abstract`, `description`, `disambiguation`, `content`, `scope`, `incipit`,
`explicit`, `prologue`, `filiation`, `incerta`, `errata`, `corrigenda`,
`record-description`, `deprecation`, `misc`.

## `idno/@type` vocabulary

Closed list: `URI`, `ISBN`, `ISSN`, `DOI`, `FIEY`, `BHS`, `BHO`, `CPG`, plus
the editorial values `redirect` and `deprecated` used for merged/superseded
records (see "URI policy" below).

## Date encoding conventions

Sources cited by Syriaca.org frequently give approximate/prose dates. Per
`documentation/dates.html`, contributors translate these into `@notBefore`/
`@notAfter` numeric ranges (or `@when` for precise single dates) using
consistent rules — useful when interpreting or filtering on date ranges
returned by `query_syriaca.py list --after/--before`:

- "Xth century" → full 100-year range (e.g. "4th century" → 0300–0400)
- "first/second half of Xth century", "early/late Xth century", "mid-Xth
  century" → 50-year range (e.g. "mid-7th century" → 0625–0675)
- "first/last quarter of Xth century" → 25-year range
- "beginning/end of Xth century" → 25-year range plus a 15-year margin into
  the adjacent century
- A trailing "?" or "probably" widens the range further (e.g. "4th
  century?" → 0250–0450, vs. 0300–0400 for plain "4th century"; "mid-7th
  century?" → 0610–0690, vs. 0625–0675 plain)
- *Circa*/*floruit* dates get proportionally larger margins — a "*fl.* Xth
  century" is rendered as a full 200-year range, deliberately not implying
  precision the sources don't support
- A single approximate year like "ca. 1842" gets a 15-year margin on each
  side (1827–1857); "shortly before/after" a date gets the same 15-year
  margin on the relevant side only
- Ranges are not mutually exclusive by design (e.g. "early" and "mid"
  overlap) — this reflects genuine source imprecision rather than a
  modeling error
- When a source gives a precise range or specific years, those are used
  directly instead of any rule above

This means a record's `notBefore`/`notAfter` should usually be read as "the
outer bound of what a specific prose date could plausibly mean," not as a
tight empirical range.

## URI policy

Per `documentation/uris.html`:

- Canonical entity URI: `http://syriaca.org/{type}/{id}` (place, person,
  work, manuscript, bibl — note bibliography entries use `bibl`, not
  `work`).
- The human-readable HTML page for a record is the entity URI + `.html`
  (e.g. `http://syriaca.org/place/78.html`).
- The TEI-XML record for an entity is the entity URI + `/tei` (e.g.
  `http://syriaca.org/place/78/tei`).
- Standalone bibliography entries (`data/bibl/tei/{id}.xml`, the ~29,000
  modern-publication citation records) are rooted at `TEI/text/body/
  biblStruct` rather than `listBibl/bibl` — this is different from the
  `works` record structure above.
- **Deprecated/merged records**: when two records for the same entity are
  merged, one is deprecated and its URI 301-redirects to the surviving
  record. The deprecated record's data is folded into the surviving one, so
  ordinary queries don't need to worry about this — but a query that might
  land on a stale/cached URI should check for `idno[@type='redirect']`
  (points to the surviving TEI record) and `idno[@type='deprecated']`.
  Deprecated records live under `data/deprecated/` and aren't covered by
  `query_syriaca.py`.

## `syriaca-tags` — the `srophe:tags` attribute vocabulary

Per `documentation/syriaca-tags.xml`, the custom `srophe:tags` attribute
(used on `persName`, `placeName`, `title`, and potentially other elements)
has three documented values:

- `#syriaca-headword` — the name used for document titles, citation, and
  disambiguation (already used by `query_syriaca.py`'s `headword()` logic).
- `#syriaca-anglicized` — an anglicized name variant added to aid searching;
  if it has no `@source`, it may not be attested in the literature and
  exists only for reader convenience.
- `#anonymous-description` — marks a name that is actually an
  editor-composed *description* standing in for an unknown proper name
  (e.g. "Anonymous 123"). These persons are also tagged with a
  `#syriaca-headword` in the form "Anonymous " + the URI number, and have a
  `trait` with value "anonymous".

## Taxonomy — `data/taxonomy/taxonomy.rdf`

An RDF/XML SKOS-ish vocabulary defining the controlled terms referenced by
`@ref` attributes elsewhere (confessions, place types, relation types). Most
of the time you don't need to parse this file — the `@ref` URI's last path
segment (e.g. `syrian-orthodox`, `broader`, `saints`) is human-readable enough
to filter or display directly, and `query_syriaca.py`'s `--confession` /
`--occupation` flags already match against it as a substring. Prefer the
authoritative vocabularies above (confessions.xml, place-types.xml) over this
file when you need the full, correctly-nested list of valid values.

## Deprecated records — `data/deprecated/`

Records superseded or merged elsewhere. Not covered by `query_syriaca.py`;
only consult this if the user is specifically chasing down a dead/old URI.
See "URI policy" above for the `idno[@type='redirect'|'deprecated']` pattern.

## Bibliography — `data/bibl/` (fetched only if requested)

~29,000 individual bibliography entries (the sources cited throughout the
other collections) in both `tei/` and `json/` form, plus a large
`fiey-bibl.xml`. This is the ~350MB chunk `setup_syriaca_data.sh` skips
unless run with `--with-bibl`. Standalone records are rooted at
`TEI/text/body/biblStruct` (see "URI policy" above), which is a different
shape from `works` records (`listBibl/bibl`) — `biblStruct` follows standard
TEI bibliographic citation structure (`analytic`/`monogr`/`series`, each
with `author`/`editor`/`title`/`imprint`). The citations visible inline in
person/place/work records (`bibl/ptr[@target]`) already give the URI of the
full entry here if it's ever needed without fetching the whole tree.
`query_syriaca.py` can `search`/`show` type `bibl` once this data is present
locally, but titles/authors are pulled generically (any `title`/`author`/
`editor` text anywhere in the `biblStruct`) rather than through a fully
modeled citation structure — treat its output as a starting point, not a
formatted citation.
