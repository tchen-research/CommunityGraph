#!/usr/bin/env python3
"""One-time: split the oversized `nla` area into rand / krylov / hpc and move
the random-matrix-theory people into the theory group. Rewrites the `area`
field in people.yaml; group labels/colors live in config.yaml."""

import yaml
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"

RAND = {  # randomized low-rank, sketching-adjacent numerical people
    "per-gunnar-martinsson", "joel-tropp", "vladimir-rokhlin", "mark-tygert",
    "ming-gu", "ethan-epperly", "robert-webber", "chris-camano",
    "alice-cortinovis", "david-persson", "daniel-kressner", "stefano-massei",
    "yuji-nakatsukasa", "taejun-park", "yijun-dong", "anna-yesypenko",
    "katherine-pearce", "ruhui-jin", "ilse-ipsen", "haim-avron",
    "petros-drineas", "michael-mahoney", "alex-townsend", "heather-wilber",
    "diana-halikias", "nicolas-boulle", "akil-narayan", "jung-eun-huh",
    "israa-fakih", "mariana-martinez-aguilar", "benjamin-carrel", "linkai-ma",
}
KRYLOV = {  # Krylov, matrix functions, matrix equations
    "anne-greenbaum", "thomas-trogdon", "tyler-chen", "yousef-saad",
    "shashanka-ubaru", "zdenek-strakos", "jorg-liesen", "stefano-pozza",
    "igor-simunec", "james-baglama", "eric-de-sturler", "valeria-simoncini",
    "daniel-szyld", "davide-palitta", "lorenzo-piccinini", "sascha-portaro",
    "andrew-higgins", "omar-de-la-cruz-cabrera", "kapil-ahuja",
    "christopher-beattie", "david-bindel", "alberto-bucci", "paul-cazeaux",
    "vasilije-perovic", "xiaoou-cheng", "jessie-chen", "abraham-khan",
    "rudi-smith",
}
HPC = {  # libraries, parallel algorithms, precision
    "james-demmel", "laura-grigori", "xiaoye-sherry-li", "zhaojun-bai",
    "julien-langou", "erin-carson", "ieva-dauzickaite", "nicholas-higham",
    "theo-mary", "edmond-chow", "sivan-toledo", "george-turkiyyah",
    "riley-murray",
}
TO_TCS = {  # random matrix theory & matrix analysis -> theory group
    "alan-edelman", "ioana-dumitriu", "ryan-schneider", "john-urschel",
    "olga-holtz",
}


def main():
    people = yaml.safe_load((DATA / "people.yaml").read_text())
    counts = {}
    for p in people:
        pid = p["id"]
        if pid in RAND:
            p["area"] = "rand"
        elif pid in KRYLOV:
            p["area"] = "krylov"
        elif pid in HPC:
            p["area"] = "hpc"
        elif pid in TO_TCS:
            p["area"] = "tcs"
        elif p.get("area") == "nla":  # anything left over defaults to krylov
            p["area"] = "krylov"
        counts[p["area"]] = counts.get(p["area"], 0) + 1

    class Dumper(yaml.SafeDumper):
        pass

    def str_rep(dumper, s):
        if "\n" in s:
            return dumper.represent_scalar("tag:yaml.org,2002:str", s, style="|")
        return dumper.represent_scalar("tag:yaml.org,2002:str", s)

    Dumper.add_representer(str, str_rep)

    header = (
        "# One entry per person. id is referenced by the other data files.\n"
        "# area: research-area group for node colors (see config.yaml node_groups).\n"
        "# Keep affiliations written consistently - the same_institution factor is\n"
        "# computed by exact (case-insensitive) match.\n"
        "# Optional keys: website, photo (direct image URL), topics (list), notes.\n"
    )
    (DATA / "people.yaml").write_text(
        header + yaml.dump(people, Dumper=Dumper, allow_unicode=True,
                           sort_keys=False, width=88))
    print("area counts:", dict(sorted(counts.items())))


if __name__ == "__main__":
    main()
