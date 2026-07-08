---
name: syriaca-query
description: Query the data behind Syriaca.org (The Syriac Reference Portal) — its Gazetteer of places, Syriac Biographical Dictionary of persons, Guide to Syriac Authors, works catalog, and SPEAR biographical factoids — by working directly with the TEI/XML records in the srophe/syriaca-data git repository. Use this whenever the user asks about Syriac places, persons, saints, authors, monasteries, dioceses, confessions/religious communities, historical relationships between places, or wants to look something up "in Syriaca," "in the Syriac Gazetteer," "in the Syriac Biographical Dictionary," or similar, even if they don't name the repository or file format explicitly. Also trigger for requests to search, filter, or cross-reference many Syriaca records at once (e.g. "all monasteries founded before 500", "every bishop of Edessa"), which the live website's search box can't do but this local-data approach can.
---

# Syriaca.org data querying

Syriaca.org publishes its scholarly data as TEI XML in the public git repository
[`srophe/syriaca-data`](https://github.com/srophe/syriaca-data). This skill works
directly against a local clone of that data rather than the live website, so it can
do things the site's search box can't: cross-reference many records, filter by
date range or confession, follow relationship graphs, and pull structured fields
straight into JSON.

## Step 0 — ask two questions before setting up data

Every time this skill starts a new task (not on every individual query within
the same task — just once at the outset), ask the user:

1. **"Do you want to include bibliographic data (`data/bibl`, ~29,000 modern
   publication citations) in this search?"** If yes, pass `--with-bibl` in
   Step 1. If no, proceed without it — citations are still visible inline in
   other records (`bibl/ptr[@target]`), just not the full cited-work record.
2. **"Should I check for updated data from Syriaca.org, or use what's already
   set up?"** If yes, (re-)run the setup script, which does a `git pull` on
   an existing clone rather than a full re-clone. If no, and a clone already
   exists (check for `data/persons/tei/`), skip straight to Step 2 and reuse
   it as-is — don't touch the network.

If this is clearly a continuation of a task from earlier in the same
conversation where these were already answered, don't re-ask — just proceed
with the same choices.

## Step 1 — get the data locally

Run the setup script. It shallow/partial/sparse-clones just the record types
this skill knows how to read, optionally including the ~350MB bibliography
tree (`data/bibl`) based on the answer to question 1 above:

```bash
bash scripts/setup_syriaca_data.sh ./syriaca-data           # without bibliography
bash scripts/setup_syriaca_data.sh ./syriaca-data --with-bibl   # with bibliography
```

This takes under a minute (longer with `--with-bibl`) and produces a
`./syriaca-data/data` directory with `persons/`, `places/`, `works/`,
`spear/`, `taxonomy/`, and optionally `bibl/` subfolders. Re-running the same
command later updates the clone (`git pull`) instead of re-cloning — this is
what "check for updated data" in Step 0 maps to.

If a clone already exists somewhere (check for a `data/persons/tei/` folder)
and the user said not to check for updates, skip straight to Step 2 and point
`--data-root` at it — no need to touch the network at all.

## Step 2 — query it

`scripts/query_syriaca.py` is a CLI over the cloned data. It uses `lxml` (already
available in this environment) and needs no other setup. All commands accept
`--data-root <path>/data`; if omitted it checks `$SYRIACA_DATA`, then
`./syriaca-data/data`, `./data`, `../data` in that order.

```bash
python3 scripts/query_syriaca.py search "edessa" --type places
python3 scripts/query_syriaca.py show place 78
python3 scripts/query_syriaca.py show person 10
python3 scripts/query_syriaca.py relations place 78 --rel-type contained-within
python3 scripts/query_syriaca.py relations person 109 --rel-name syriaca:born-at
python3 scripts/query_syriaca.py list places --place-type monastery --confession "syrian orthodox"
python3 scripts/query_syriaca.py list persons --occupation bishop --after 400 --before 600
python3 scripts/query_syriaca.py factoids 3218 --subtype occupation
python3 scripts/query_syriaca.py search "brooks" --type bibl   # only works if --with-bibl was fetched
```

Every subcommand prints JSON to stdout, so pipe into `jq`, `python3 -c "..."`, or
just read it directly to answer the user's question. Run
`python3 scripts/query_syriaca.py <subcommand> -h` for the full flag list — the
tool is self-documenting.

### Subcommand cheat sheet

- **search** `<query>` — keyword search across names/titles (person, place, work,
  or all three by default; pass `--type bibl` explicitly to search bibliography
  entries, which are excluded from the "all" default). Use this first when the
  user gives a name and you need the numeric id. Matches are substring,
  case-insensitive, across every language variant of the name (English, Syriac,
  Arabic, etc.) — pass `--lang en` to restrict (see `references/schema.md` for
  the full closed list of valid `xml:lang` values, including script-variant
  codes like `syr-Syrj` for East Syriac script and `ar-Syrc` for Garshuni).
- **show** `<type> <id>` — full structured summary of one record: all name
  variants, abstract/description, dates (floruit/birth/death or
  existence/events), confessions or occupations, coordinates for places.
  `<type>` is `person`, `place`, `work`, `spear`, or `bibl`; `<id>` is the
  number from the record's URI (`http://syriaca.org/place/78` → `78`).
- **list** `<person|place>` — scans the *entire* corpus of that type and filters
  by confession, occupation (persons only), place type, containment, or date
  range. This is the tool for "all X" or "every Y" questions. Start narrow
  (`--limit` defaults are already conservative) and widen if the user wants more.
  For `--place-type`, the full closed vocabulary (25 values with definitions)
  is in `references/schema.md` — it includes several types easy to miss, like
  `cemetery`, `composite`, `madrasa`, and `valley`.
- **relations** `<type> <id>` — the relation graph edges for one record. Filter
  by broad category with `--rel-type` (e.g. `contained-within`,
  `disambiguation`) or by the specific relationship with `--rel-name` (e.g.
  `syriaca:born-at`, `syriaca:died-at`, `syriaca:possibly-identical`,
  `syriaca:share-a-name` — see `references/schema.md` for the full documented
  vocabulary, plus the `snap:` prefixed prosopographical relations). Each edge
  reports direction and the URI of the other party — pair with `show` to get
  that party's name.
- **factoids** `<person_id>` — SPEAR (Syriac Persons, Events, and Relations)
  factoids: discrete, individually-cited biographical claims about a person
  (occupation, gender, religious affiliation, name variants, relationships to
  other people/places). Useful when `show person` isn't detailed enough or the
  user wants to see what's independently attested vs. synthesized.

### Worked example

User asks: "What Syriac Orthodox monasteries near Edessa does Syriaca.org know
about, and when were they founded?"

1. `search "edessa" --type places` to find Edessa's id (78).
2. `relations place 78 --rel-type contained-within` and/or `list places
   --place-type monastery --contained-within 2775` (Edessa's containing region)
   to find candidate monasteries — note not everything nearby is literally
   "contained-within" Edessa itself, so also try a broader region id if the
   first pass comes up short.
3. `show place <id>` on each hit to pull the `states` (existence dates,
   confession) and `abstract` fields, then compose the answer with citations
   back to the `uri` field (Syriaca's canonical, citable identifier).

## Data model at a glance

Every record type lives at `data/<type>/tei/<id>.xml` and has a canonical URI
`http://syriaca.org/<type>/<id>`:

| Type | Directory | Contains |
|---|---|---|
| person | `persons/tei/` | Biographical Dictionary + Authors entries |
| place | `places/tei/` | Syriac Gazetteer entries |
| work | `works/tei/` | Titles/editions of Syriac texts (BHS, CBSS-linked) |
| spear | `spear/tei/` | SPEAR factoids — atomic, cited claims about persons |
| bibl | `bibl/tei/` | Modern-publication bibliography entries (only present if fetched with `--with-bibl`; different record shape — `biblStruct`, not `listBibl/bibl`) |

For the full field-by-field XML structure (namespaces, which elements hold
dates vs. confessions vs. relations, the complete controlled vocabularies for
place types, confessions, relation names, note/idno types, and `xml:lang`
codes), see `references/schema.md` — read it before writing any custom XPath
beyond what `query_syriaca.py` already covers.

## When to go beyond the CLI

`query_syriaca.py` covers the common cases, but the data is just XML — for a
one-off need it doesn't support (e.g. a very specific XPath, filtering works
by subject classification, or a fully-modeled bibliographic citation from
`data/bibl`), read `references/schema.md` for the namespace/element
reference, then write a short ad hoc script with `lxml` against the same
`data/` tree rather than trying to bend the CLI to fit.

## A note on the live site vs. this local copy

Syriaca.org also exposes a REST search API, a GeoJSON/KML gazetteer API, and an
OAI-PMH harvesting endpoint at syriaca.org itself, plus a SPARQL endpoint over
an RDF conversion of this same data. This skill deliberately works from the git
repository instead: it's faster for bulk/cross-referencing queries, works
offline once cloned, and gives direct access to the full TEI markup (sources,
uncertainty, alternate readings) that the JSON/API views simplify away. If the
user specifically wants the live site's search-relevance ranking, GeoJSON/KML
output, or SPARQL graph queries, that's a different task from what this skill
does — say so rather than silently substituting the local data.
