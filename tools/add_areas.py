#!/usr/bin/env python3
"""One-time: add `area` to every person in people.yaml."""
import yaml
from pathlib import Path

PEOPLE = Path("/home/tyler/Documents/Research Code/NLA_graph/data/people.yaml")

TCS = {
    "aaron-sidford", "ainesh-bakshi", "cameron-musco", "christopher-musco",
    "david-woodruff", "edo-liberty", "jelani-nelson", "josh-alman",
    "kenneth-clarkson", "lorenzo-beretta", "michael-kapralov",
    "michal-derezinski", "noah-amsel", "peng-zhang", "raphael-meyer",
    "rasmus-kyng", "ravindran-kannan", "richard-peng", "rikhav-shah",
    "santosh-vempala", "sushant-sachdeva", "tamas-sarlos",
    "nikhil-srivastava", "jorge-garza-vargas",
}
OPT = {
    "deanna-needell", "anna-ma", "jamie-haddock", "elizaveta-rebrova",
    "jackie-lok", "robert-gower", "fred-roosta", "mert-pilanci",
    "rachel-ward", "madeleine-udell", "swati-padmanabhan", "vivak-patel",
    "shancong-mou", "giulio-trigila",
}
INVERSE = {
    "misha-kilmer", "julianne-chung", "matthias-chung", "elizabeth-newman",
    "arvind-saibaba", "lothar-reichel", "daniela-calvetti", "erkki-somersalo",
    "mirjeta-pasha", "lucas-onisk", "malena-espanol", "malena-sabate-landman",
    "andrea-arnold", "andreas-mang", "harbir-antil", "abhijit-chowdhary",
    "mitchell-scott", "fan-tian", "ansley-bentley", "fatoumata-sanogo",
    "lior-horesh", "nick-polydorides", "vishwas-rao",
}


def area_of(pid):
    if pid in TCS:
        return "tcs"
    if pid in OPT:
        return "opt"
    if pid in INVERSE:
        return "inverse"
    return "nla"


class Dumper(yaml.SafeDumper):
    pass


def str_rep(dumper, s):
    if "\n" in s:
        return dumper.represent_scalar("tag:yaml.org,2002:str", s, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", s)


Dumper.add_representer(str, str_rep)

people = yaml.safe_load(PEOPLE.read_text())
for p in people:
    # insert area right after affiliation for readability
    items = list(p.items())
    p.clear()
    for k, v in items:
        p[k] = v
        if k == "affiliation":
            p["area"] = area_of(p["id"])

header = (
    "# One entry per person. id is referenced by the other data files.\n"
    "# area: research-area group for node colors (see config.yaml node_groups).\n"
    "# Keep affiliations written consistently - the same_institution factor is\n"
    "# computed by exact (case-insensitive) match.\n"
    "# Optional keys: website, photo (direct image URL), topics (list), notes.\n"
)
PEOPLE.write_text(header + yaml.dump(people, Dumper=Dumper, allow_unicode=True,
                                     sort_keys=False, width=88))
print(f"areas added to {len(people)} people")
