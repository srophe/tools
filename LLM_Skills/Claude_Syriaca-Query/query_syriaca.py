#!/usr/bin/env python3
"""
query_syriaca.py - Search and inspect Syriaca.org's TEI/XML data from a local
clone of the srophe/syriaca-data git repository.

Data model (see references/schema.md in the skill for full detail):
  data/persons/tei/{id}.xml   TEI/text/body/listPerson/person
  data/places/tei/{id}.xml    TEI/text/body/listPlace/place
  data/works/tei/{id}.xml     TEI/text/body/listBibl/bibl[@xml:id^="work-"]
  data/spear/tei/{id}.xml     TEI/text/body/ab[@type="factoid"]  (SPEAR factoids)
  data/bibl/tei/{id}.xml      TEI/text/body/biblStruct  (only present if fetched
                               with --with-bibl; modern-publication citations,
                               a different record shape from "works" above)
  data/taxonomy/taxonomy.rdf  RDF vocabulary for confessions/place-types/relations

Every record has a canonical URI of the form
http://syriaca.org/{person,place,work,spear,bibl}/{id}.

Subcommands:
  search      Full-text keyword search across names/titles (and optionally descriptions)
  show        Print a structured summary of one record by type + numeric id
  list        List/filter records of one type by confession, place-type, date range, etc.
  relations   List the relation edges of a record; filter by broad @type or
              specific @name (e.g. syriaca:born-at) -- see references/schema.md
              for the documented vocabulary of relation names.
  factoids    List SPEAR factoids (biographical claims + citations) about a person

Run `query_syriaca.py <subcommand> -h` for per-command options.
"""
import argparse
import glob
import os
import re
import sys
import json
from lxml import etree

NS = {"tei": "http://www.tei-c.org/ns/1.0", "srophe": "https://srophe.app"}

TYPE_INFO = {
    "person": {"dir": "persons", "record_xpath": ".//tei:listPerson/tei:person", "name_el": "persName", "uri_prefix": "http://syriaca.org/person/"},
    "place": {"dir": "places", "record_xpath": ".//tei:listPlace/tei:place", "name_el": "placeName", "uri_prefix": "http://syriaca.org/place/"},
    "work": {"dir": "works", "record_xpath": ".//tei:listBibl/tei:bibl[starts-with(@xml:id,'work-')]", "name_el": "title", "uri_prefix": "http://syriaca.org/work/"},
    "spear": {"dir": "spear", "record_xpath": ".//tei:ab[@type='factoid']", "name_el": None, "uri_prefix": "http://syriaca.org/spear/"},
    # bibl records only exist locally if setup_syriaca_data.sh was run with --with-bibl.
    # Root element is biblStruct (standard TEI bibliographic citation structure), not
    # listBibl/bibl like "work" -- see references/schema.md "URI policy" / "Bibliography".
    "bibl": {"dir": "bibl", "record_xpath": ".//tei:biblStruct", "name_el": None, "uri_prefix": "http://syriaca.org/bibl/"},
}

ALIASES = {
    "persons": "person", "places": "place", "works": "work",
    "factoids": "spear", "spear-factoids": "spear",
    "bibls": "bibl", "bibliography": "bibl", "biblio": "bibl",
}


def resolve_type(t):
    t = t.rstrip("s") if t not in TYPE_INFO and t.rstrip("s") in TYPE_INFO else t
    t = ALIASES.get(t, t)
    if t not in TYPE_INFO:
        raise SystemExit(f"Unknown type '{t}'. Expected one of: person, place, work, spear, bibl")
    return t


def data_root(explicit):
    if explicit:
        return explicit
    env = os.environ.get("SYRIACA_DATA")
    if env:
        return env
    for candidate in ("./syriaca-data/data", "./data", "../data"):
        if os.path.isdir(candidate):
            return candidate
    raise SystemExit(
        "Could not find the syriaca-data checkout. Pass --data-root, set $SYRIACA_DATA, "
        "or run scripts/setup_syriaca_data.sh first."
    )


def iter_files(root, type_key):
    d = os.path.join(root, TYPE_INFO[type_key]["dir"], "tei")
    if not os.path.isdir(d):
        hint = " (fetch it with setup_syriaca_data.sh --with-bibl)" if type_key == "bibl" else ""
        raise SystemExit(f"Expected directory not found: {d}{hint} (did setup finish? is --data-root correct?)")
    for path in sorted(glob.glob(os.path.join(d, "*.xml")), key=lambda p: (len(p), p)):
        yield path


_PARSER = etree.XMLParser(recover=True)  # a handful of records have minor id-uniqueness quirks; tolerate them


def parse(path):
    try:
        tree = etree.parse(path, parser=_PARSER)
    except etree.XMLSyntaxError as e:
        print(f"warning: could not parse {path}: {e}", file=sys.stderr)
        return None
    if tree.getroot() is None:
        print(f"warning: could not parse {path} (unrecoverable)", file=sys.stderr)
        return None
    return tree


def desc_text(state_el):
    """Text of a <desc> child if present, else the element's own text."""
    desc = state_el.find("tei:desc", namespaces=NS)
    return clean_text(desc) if desc is not None else clean_text(state_el)


def record_id_from_path(path):
    return os.path.splitext(os.path.basename(path))[0]


def get_records(tree, type_key):
    """Yield each record element in a file (usually one, occasionally more)."""
    return tree.getroot().findall(TYPE_INFO[type_key]["record_xpath"], namespaces=NS)


def headword(record, name_el):
    """Prefer the name tagged as the syriaca-headword; else the first name; else joined text."""
    if name_el is None:
        return None
    names = record.findall(f"tei:{name_el}", namespaces=NS)
    if not names:
        return None
    for n in names:
        if "syriaca-headword" in (n.get("{https://srophe.app}tags") or ""):
            return clean_text(n)
    return clean_text(names[0])


def clean_text(el):
    if el is None:
        return None
    return re.sub(r"\s+", " ", "".join(el.itertext())).strip()


def all_names(record, name_el):
    if name_el is None:
        return []
    out = []
    for n in record.findall(f"tei:{name_el}", namespaces=NS):
        txt = clean_text(n)
        if txt:
            out.append({"lang": n.get("{http://www.w3.org/XML/1998/namespace}lang"), "text": txt})
    return out


def bibl_titles(record):
    """bibl (biblStruct) records nest titles inside analytic/monogr/series rather
    than repeating a single top-level element, so this collects any <title>
    text anywhere in the record instead of relying on a fixed name_el."""
    out = []
    for t in record.findall(".//tei:title", namespaces=NS):
        txt = clean_text(t)
        if txt:
            out.append({"lang": t.get("{http://www.w3.org/XML/1998/namespace}lang"), "text": txt})
    return out


def record_uri(record, type_key, fallback_id):
    prefix = TYPE_INFO[type_key]["uri_prefix"]
    idnos = record.findall("tei:idno[@type='URI']", namespaces=NS)
    if not idnos:
        # bibl (and occasionally other types) may nest idno deeper than a direct child
        idnos = record.findall(".//tei:idno[@type='URI']", namespaces=NS)
    for idno in idnos:
        uri = (idno.text or "").strip()
        if uri.startswith(prefix):
            return uri
    return prefix + fallback_id


# ---------------------------------------------------------------------------
# search
# ---------------------------------------------------------------------------

def cmd_search(args):
    root = data_root(args.data_root)
    types = [resolve_type(args.type)] if args.type != "all" else ["person", "place", "work"]
    q = args.query.lower()
    results = []
    for type_key in types:
        name_el = TYPE_INFO[type_key]["name_el"]
        for path in iter_files(root, type_key):
            tree = parse(path)
            if tree is None:
                continue
            file_id = record_id_from_path(path)
            for rec in get_records(tree, type_key):
                names = bibl_titles(rec) if type_key == "bibl" else all_names(rec, name_el)
                for n in names:
                    if args.lang and n["lang"] != args.lang:
                        continue
                    if q in n["text"].lower():
                        results.append({
                            "type": type_key,
                            "id": file_id,
                            "uri": record_uri(rec, type_key, file_id),
                            "matched_name": n["text"],
                            "lang": n["lang"],
                            "headword": (names[0]["text"] if type_key == "bibl" and names else headword(rec, name_el)),
                        })
                        break
            if len(results) >= args.limit:
                break
        if len(results) >= args.limit:
            break
    print(json.dumps(results[: args.limit], ensure_ascii=False, indent=2))


# ---------------------------------------------------------------------------
# show
# ---------------------------------------------------------------------------

def text_or_none(el):
    return clean_text(el) if el is not None else None


def summarize_person(rec):
    out = {"names": all_names(rec, "persName")}
    abstract = rec.find("tei:note[@type='abstract']", namespaces=NS)
    out["abstract"] = text_or_none(abstract)
    floruit = rec.find("tei:floruit/tei:date", namespaces=NS)
    if floruit is not None:
        out["floruit"] = {k: floruit.get(k) for k in ("when", "notBefore", "notAfter") if floruit.get(k)}
        out["floruit"]["text"] = clean_text(floruit)
    for tag in ("birth", "death"):
        el = rec.find(f"tei:{tag}", namespaces=NS)
        if el is not None:
            date = el.find("tei:date", namespaces=NS)
            place = el.find("tei:placeName", namespaces=NS)
            entry = {}
            if date is not None:
                entry["date"] = clean_text(date)
                for k in ("when", "notBefore", "notAfter"):
                    if date.get(k):
                        entry[k] = date.get(k)
            if place is not None:
                entry["place"] = clean_text(place)
                entry["place_ref"] = place.get("ref")
            if entry:
                out[tag] = entry
    gender = rec.find("tei:gender", namespaces=NS)
    if gender is not None:
        out["gender"] = clean_text(gender)
    states = []
    for st in rec.findall("tei:state", namespaces=NS):
        desc = st.find("tei:desc", namespaces=NS)
        states.append({"type": st.get("type"), "ref": st.get("ref"), "desc": clean_text(desc)})
    if states:
        out["states"] = states
    return out


def summarize_place(rec):
    out = {"place_type": rec.get("type"), "names": all_names(rec, "placeName")}
    abstract = rec.find("tei:desc[@type='abstract']", namespaces=NS)
    out["abstract"] = text_or_none(abstract)
    coords = rec.find("tei:location[@type='gps']/tei:geo", namespaces=NS)
    if coords is not None and coords.text:
        parts = coords.text.split()
        if len(parts) == 2:
            out["coordinates"] = {"lat": parts[0], "long": parts[1]}
    states = []
    for st in rec.findall("tei:state", namespaces=NS):
        desc = st.find("tei:desc", namespaces=NS)
        states.append({
            "type": st.get("type"), "ref": st.get("ref"),
            "from": st.get("from"), "to": st.get("to"),
            "desc": clean_text(desc),
        })
    if states:
        out["states"] = states
    events = []
    for ev in rec.findall("tei:event", namespaces=NS):
        desc = ev.find("tei:desc", namespaces=NS)
        events.append({"when": ev.get("when"), "notBefore": ev.get("notBefore"), "notAfter": ev.get("notAfter"), "desc": clean_text(desc)})
    if events:
        out["events"] = events
    return out


def summarize_work(rec):
    out = {"names": all_names(rec, "title")}
    # bibl/@subtype on a work record is one of original-composition, revision,
    # translation -- see references/schema.md "Works".
    if rec.get("subtype"):
        out["subtype"] = rec.get("subtype")
    author = rec.find("tei:author", namespaces=NS)
    if author is not None:
        out["author"] = clean_text(author)
        out["author_ref"] = author.get("ref")
    # note/@type is a closed vocabulary (incipit, explicit, prologue, content,
    # scope, filiation, incerta, errata, corrigenda, misc, ...) -- surface
    # whatever is actually present rather than assuming specific types exist.
    notes = []
    for n in rec.findall("tei:note", namespaces=NS):
        txt = clean_text(n)
        if txt:
            notes.append({"type": n.get("type"), "text": txt})
    if notes:
        out["notes"] = notes
    idnos = []
    for idno in rec.findall("tei:idno", namespaces=NS):
        txt = (idno.text or "").strip()
        if txt:
            idnos.append({"type": idno.get("type"), "value": txt})
    if idnos:
        out["idnos"] = idnos
    return out


def summarize_spear(rec):
    out = {"subtype": rec.get("subtype"), "id": rec.get("{http://www.w3.org/XML/1998/namespace}id")}
    persons = []
    for p in rec.findall(".//tei:persName", namespaces=NS):
        persons.append({"ref": p.get("ref"), "text": clean_text(p)})
    out["persons"] = persons
    note = rec.find(".//tei:note[@type='desc']", namespaces=NS)
    out["claim"] = text_or_none(note) or clean_text(rec)
    bibls = []
    for b in rec.findall("tei:bibl", namespaces=NS):
        ptr = b.find("tei:ptr", namespaces=NS)
        cited = b.find("tei:citedRange", namespaces=NS)
        bibls.append({"source": ptr.get("target") if ptr is not None else None, "cited": clean_text(cited)})
    if bibls:
        out["citations"] = bibls
    return out


def summarize_bibl(rec):
    """bibl records are TEI biblStruct citations (analytic/monogr/series), a
    different shape from every other record type here -- see
    references/schema.md "Bibliography". This pulls title/author/editor/date
    generically rather than modeling the full citation structure, so treat
    the output as a starting point rather than a formatted citation."""
    out = {"titles": bibl_titles(rec)}
    contributors = []
    for tag in ("author", "editor"):
        for el in rec.findall(f".//tei:{tag}", namespaces=NS):
            txt = clean_text(el)
            if txt:
                contributors.append({"role": tag, "text": txt, "ref": el.get("ref")})
    if contributors:
        out["contributors"] = contributors
    date = rec.find(".//tei:date", namespaces=NS)
    if date is not None:
        entry = {"text": clean_text(date)}
        for k in ("when", "notBefore", "notAfter"):
            if date.get(k):
                entry[k] = date.get(k)
        out["date"] = entry
    idnos = []
    for idno in rec.findall(".//tei:idno", namespaces=NS):
        txt = (idno.text or "").strip()
        if txt:
            idnos.append({"type": idno.get("type"), "value": txt})
    if idnos:
        out["idnos"] = idnos
    return out


SUMMARIZERS = {"person": summarize_person, "place": summarize_place, "work": summarize_work, "spear": summarize_spear, "bibl": summarize_bibl}


def cmd_show(args):
    root = data_root(args.data_root)
    type_key = resolve_type(args.type)
    path = os.path.join(root, TYPE_INFO[type_key]["dir"], "tei", f"{args.id}.xml")
    if not os.path.isfile(path):
        raise SystemExit(f"No {type_key} record for id {args.id} at {path}")
    tree = parse(path)
    records = get_records(tree, type_key)
    if not records:
        raise SystemExit(f"File {path} has no {type_key} record elements (schema may differ from expectations).")
    out = []
    for rec in records:
        summary = SUMMARIZERS[type_key](rec)
        summary["uri"] = record_uri(rec, type_key, args.id)
        out.append(summary)
    print(json.dumps(out if len(out) > 1 else out[0], ensure_ascii=False, indent=2))


# ---------------------------------------------------------------------------
# list (filtered corpus scan)
# ---------------------------------------------------------------------------

def year_of(val):
    if not val:
        return None
    try:
        return int(re.sub(r"^-", "-", val)[:5].lstrip("0") or "0") if val.startswith("-") else int(val[:4])
    except ValueError:
        return None


def in_range(rec_from, rec_to, after, before):
    f, t = year_of(rec_from), year_of(rec_to)
    if after is not None and t is not None and t < after:
        return False
    if before is not None and f is not None and f > before:
        return False
    return True


def cmd_list(args):
    root = data_root(args.data_root)
    type_key = resolve_type(args.type)
    name_el = TYPE_INFO[type_key]["name_el"]
    results = []
    for path in iter_files(root, type_key):
        tree = parse(path)
        if tree is None:
            continue
        file_id = record_id_from_path(path)
        for rec in get_records(tree, type_key):
            if type_key == "place":
                if args.place_type and rec.get("type") != args.place_type:
                    continue
                if args.confession:
                    states = rec.findall("tei:state[@type='confession']", namespaces=NS)
                    if not any(args.confession.lower() in (s.get("ref") or "").lower() or args.confession.lower() in desc_text(s).lower() for s in states):
                        continue
                if args.contained_within:
                    target = args.contained_within if args.contained_within.startswith("http") else f"http://syriaca.org/place/{args.contained_within}"
                    rels = rec.getparent().findall("tei:listRelation/tei:relation[@type='contained-within']", namespaces=NS)
                    if not any(r.get("passive") == target for r in rels):
                        continue
                if args.after or args.before:
                    ex = rec.find("tei:state[@type='existence']", namespaces=NS)
                    if ex is None or not in_range(ex.get("from"), ex.get("to"), args.after, args.before):
                        continue
            elif type_key == "person":
                if args.confession:
                    states = rec.findall("tei:state[@type='religious-affiliation']", namespaces=NS)
                    if not any(args.confession.lower() in (s.get("ref") or "").lower() or args.confession.lower() in desc_text(s).lower() for s in states):
                        continue
                if args.occupation:
                    states = rec.findall("tei:state[@type='occupation']", namespaces=NS)
                    if not any(args.occupation.lower() in desc_text(s).lower() for s in states):
                        continue
                if args.after or args.before:
                    fl = rec.find("tei:floruit/tei:date", namespaces=NS)
                    if fl is None or not in_range(fl.get("notBefore") or fl.get("when"), fl.get("notAfter") or fl.get("when"), args.after, args.before):
                        continue
            results.append({
                "type": type_key,
                "id": file_id,
                "uri": record_uri(rec, type_key, file_id),
                "headword": headword(rec, name_el),
            })
            if len(results) >= args.limit:
                break
        if len(results) >= args.limit:
            break
    print(json.dumps(results, ensure_ascii=False, indent=2))


# ---------------------------------------------------------------------------
# relations
# ---------------------------------------------------------------------------

def cmd_relations(args):
    root = data_root(args.data_root)
    type_key = resolve_type(args.type)
    path = os.path.join(root, TYPE_INFO[type_key]["dir"], "tei", f"{args.id}.xml")
    if not os.path.isfile(path):
        raise SystemExit(f"No {type_key} record for id {args.id} at {path}")
    tree = parse(path)
    self_uri = TYPE_INFO[type_key]["uri_prefix"] + args.id
    out = []
    for rel in tree.getroot().findall(".//tei:relation", namespaces=NS):
        rel_type = rel.get("type")
        rel_name = rel.get("name")
        if args.rel_type and rel_type != args.rel_type:
            continue
        if args.rel_name and rel_name != args.rel_name:
            continue
        desc = rel.find("tei:desc", namespaces=NS)
        entry = {"name": rel_name, "type": rel_type, "taxonomy_ref": rel.get("ref"), "desc": clean_text(desc)}
        if rel.get("active") or rel.get("passive"):
            active, passive = rel.get("active"), rel.get("passive")
            entry["direction"] = "outgoing" if active == self_uri else "incoming" if passive == self_uri else "unknown"
            entry["other"] = passive if active == self_uri else active
        elif rel.get("mutual"):
            others = [u for u in rel.get("mutual").split() if u != self_uri]
            entry["other"] = others[0] if len(others) == 1 else others
        out.append(entry)
    print(json.dumps(out, ensure_ascii=False, indent=2))


# ---------------------------------------------------------------------------
# factoids (SPEAR)
# ---------------------------------------------------------------------------

def cmd_factoids(args):
    root = data_root(args.data_root)
    person_uri = args.person_id if args.person_id.startswith("http") else f"http://syriaca.org/person/{args.person_id}"
    out = []
    for path in iter_files(root, "spear"):
        tree = parse(path)
        if tree is None:
            continue
        for ab in tree.getroot().findall(".//tei:ab[@type='factoid']", namespaces=NS):
            if args.subtype and ab.get("subtype") != args.subtype:
                continue
            refs = [p.get("ref") for p in ab.findall(".//tei:persName", namespaces=NS)]
            if person_uri not in refs:
                continue
            out.append(summarize_spear(ab))
    print(json.dumps(out, ensure_ascii=False, indent=2))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--data-root", help="Path to the syriaca-data 'data/' directory (default: $SYRIACA_DATA or ./syriaca-data/data)")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("search", help="Full-text search over names/titles")
    s.add_argument("query")
    s.add_argument("--type", default="all", choices=["all", "person", "place", "work", "persons", "places", "works", "bibl", "bibls"])
    s.add_argument("--lang", help="Restrict to an xml:lang value, e.g. en, syr, ar, syr-Syrj (see references/schema.md for the full closed list)")
    s.add_argument("--limit", type=int, default=25)
    s.set_defaults(func=cmd_search)

    g = sub.add_parser("show", help="Print a structured summary of one record")
    g.add_argument("type", choices=list(TYPE_INFO) + list(ALIASES))
    g.add_argument("id", help="Numeric id (the N in http://syriaca.org/place/N)")
    g.set_defaults(func=cmd_show)

    l = sub.add_parser("list", help="List/filter records of one type across the whole corpus")
    l.add_argument("type", choices=["person", "place", "persons", "places"])
    l.add_argument("--confession", help="Match a confession/religious-affiliation name or taxonomy ref substring")
    l.add_argument("--occupation", help="(persons) match an occupation description substring")
    l.add_argument("--place-type", help="(places) one of the 25 controlled values, e.g. monastery, church, settlement, diocese, cemetery, composite, madrasa, valley -- full list in references/schema.md")
    l.add_argument("--contained-within", help="(places) numeric id or URI of a containing place")
    l.add_argument("--after", type=int, help="Only records attested/existing after this year")
    l.add_argument("--before", type=int, help="Only records attested/existing before this year")
    l.add_argument("--limit", type=int, default=50)
    l.set_defaults(func=cmd_list)

    r = sub.add_parser("relations", help="List relation edges for a record; filter by broad @type or specific @name")
    r.add_argument("type", choices=list(TYPE_INFO) + list(ALIASES))
    r.add_argument("id")
    r.add_argument("--rel-type", help="Filter to one broad relation @type, e.g. contained-within, disambiguation")
    r.add_argument("--rel-name", help="Filter to one specific relation @name, e.g. syriaca:born-at, syriaca:died-at, syriaca:possibly-identical (see references/schema.md for the documented vocabulary)")
    r.set_defaults(func=cmd_relations)

    f = sub.add_parser("factoids", help="List SPEAR factoids (sourced biographical claims) about a person")
    f.add_argument("person_id", help="Numeric person id or full http://syriaca.org/person/N URI")
    f.add_argument("--subtype", help="Filter to one factoid subtype, e.g. occupation, gender, religious-affiliation")
    f.set_defaults(func=cmd_factoids)

    return p


def main():
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
