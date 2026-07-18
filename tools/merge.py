#!/usr/bin/env python3
"""One-time scaffolding: merge the two raw workshop rosters into
data/people.yaml and data/workshops.yaml. After this runs, the YAML files in
data/ are the source of truth and are edited by hand."""

import re
import unicodedata
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
OUT = Path("/home/tyler/Documents/Research Code/NLA_graph/data")

# name-as-listed -> canonical display name
CANON_NAME = {
    "Chris Musco": "Christopher Musco",
    "Rob Webber": "Robert Webber",
    "Michal Derezinski": "Michał Dereziński",
    "Michal Dereziński": "Michał Dereziński",
    "Sherry Xiaoye Li": "Xiaoye Sherry Li",
    "Nicolas Boulle": "Nicolas Boullé",
    "Peter Burgisser": "Peter Bürgisser",
    "Zdenek Strakos": "Zdeněk Strakoš",
    "Malena Espanol": "Malena Español",
    "Joerg Liesen": "Jörg Liesen",
    "Theo Mary": "Théo Mary",
    "Malena Sabate Landman": "Malena Sabaté Landman",
    "Ieva Dauzickaite": "Ieva Daužickaitė",
    "Jim Demmel": "James Demmel",
    "Nick Higham": "Nicholas Higham",
    "Carlos Beltran": "Carlos Beltrán",
    "Arvind Krishna Saibaba": "Arvind Saibaba",
}

# affiliation-as-listed -> canonical (also used so same_institution matching works)
CANON_AFF = {
    "Berkeley": "University of California, Berkeley",
    "UC Berkeley": "University of California, Berkeley",
    "University of California Berkeley": "University of California, Berkeley",
    "CMU": "Carnegie Mellon University",
    "U Washington": "University of Washington",
    "UT Austin": "University of Texas at Austin",
    "Caltech": "California Institute of Technology",
    "NYU": "New York University",
    "Oxford University": "University of Oxford",
    "MIT": "Massachusetts Institute of Technology",
    "EPFL": "EPFL",
    "École Polytechnique Fédérale de Lausanne": "EPFL",
    "Ecole Polytechnique Federale de Lausanne": "EPFL",
    "EPFL/PSI": "EPFL / Paul Scherrer Institut",
    "Stanford university": "Stanford University",
    "Stanford Univrsity": "Stanford University",
    "UC San Diego": "University of California, San Diego",
    "University of California San Diego": "University of California, San Diego",
    "Princeton": "Princeton University",
    "UCLA": "University of California, Los Angeles",
    "Universita' di Bologna": "University of Bologna",
    "Università di Bologna": "University of Bologna",
    "Alma Mater Studiorum - Università di Bologna": "University of Bologna",
    "Alma Mater Studiorum, Universita' di Bologna": "University of Bologna",
    "Alma Mater Studiorum, Università di Bologna": "University of Bologna",
    "Charles University, Prague": "Charles University",
    "Simons Institute/NYU": "New York University",
    "New York University & Flatiron Institute": "New York University / Flatiron Institute",
    "Technical University of Berlin": "TU Berlin",
    "UMass Amherst": "University of Massachusetts Amherst",
    "The Hong Kong University of Science and Technology": "Hong Kong University of Science and Technology",
    "KAUST -- King Abdullah University of Science and Technology": "KAUST",
    "University of Wisconsin -- Madison": "University of Wisconsin–Madison",
    "IBM Research & Oden Institute, UT Austin": "IBM Research",
    "ICERM": "ICERM / Brown University",
    "University of Manchester": "University of Manchester",
}

# people whose listed affiliation is stale; current one (mid-2026) as best known
AFF_OVERRIDE = {
    "raphael-meyer": "California Institute of Technology",
    "nicolas-boulle": "Imperial College London",
    "ieva-dauzickaite": "CERFACS",
    "jackie-lok": "National University of Singapore",
}

# People added by hand: core RandNLA figures not on either participant list.
ADDED = [
    ("Rachel Ward", "University of Texas at Austin"),
    ("Riley Murray", "Sandia National Laboratories"),
    ("Kenneth Clarkson", "IBM Research"),
    ("Vladimir Rokhlin", "Yale University"),
    ("Mark Tygert", "Meta"),
    ("Jelani Nelson", "University of California, Berkeley"),
    ("Tamás Sarlós", "Google Research"),
    ("Mert Pilanci", "Stanford University"),
    ("Ravindran Kannan", "Simons Institute / Indian Institute of Science"),
    ("Edo Liberty", "Pinecone"),
    ("Ming Gu", "University of California, Berkeley"),
    ("Agnieszka Miedlar", "Virginia Tech"),
]

# topics / notes for well-known members (kept short; extend freely in people.yaml)
CURATED = {
    "petros-drineas": (["sketching", "CUR & leverage scores", "RandNLA foundations"],
        "One of the founders of RandNLA: early Monte Carlo algorithms for matrix "
        "multiplication and CUR, and the 2016 CACM survey with Mahoney. "
        "Co-organizer of the ICERM 2026 workshop."),
    "michael-mahoney": (["leverage scores", "RandNLA foundations", "ML & scientific computing"],
        "One of the founders of RandNLA; leverage-score sampling, implicit "
        "regularization, and the RandLAPACK effort."),
    "per-gunnar-martinsson": (["randomized SVD", "fast direct solvers", "rank-structured matrices"],
        "Co-author of the Halko–Martinsson–Tropp randomized SVD survey (SIREV 2011) "
        "and the Acta Numerica 2020 RandNLA survey."),
    "joel-tropp": (["matrix concentration", "randomized algorithms", "sketching"],
        "Matrix concentration inequalities; HMT randomized SVD survey; Acta Numerica "
        "2020 survey with Martinsson."),
    "david-woodruff": (["sketching", "streaming", "lower bounds"],
        "Sketching-as-a-tool; Clarkson–Woodruff input-sparsity-time regression and "
        "low-rank approximation."),
    "ilse-ipsen": (["perturbation theory", "leverage scores", "probabilistic numerics"],
        "Numerical analysis of randomized algorithms; leverage scores and "
        "probabilistic bounds."),
    "yousef-saad": (["Krylov methods", "preconditioning", "spectrum estimation"],
        "Krylov subspace methods; stochastic spectrum estimation line with Ubaru."),
    "anne-greenbaum": (["Krylov methods", "finite precision"],
        "Foundational analysis of Krylov methods in finite precision arithmetic."),
    "thomas-trogdon": (["random matrices", "universality"],
        "Random matrix theory and universality in the runtime of numerical algorithms."),
    "tyler-chen": (["Lanczos", "stochastic trace estimation", "matrix functions"],
        "Lanczos-based methods for matrix functions and trace estimation; finite "
        "precision behavior of Krylov methods."),
    "cameron-musco": (["sublinear algorithms", "spectral methods"],
        "Randomized block Krylov methods, Hutch++, sublinear-time linear algebra. "
        "Brother of Christopher."),
    "christopher-musco": (["randomized Krylov", "trace estimation", "matvec query complexity"],
        "Randomized block Krylov methods, Hutch++, matrix-vector query complexity. "
        "Brother of Cameron."),
    "daniel-kressner": (["low-rank approximation", "tensors", "eigenvalue problems"],
        "Low-rank and tensor methods; randomized trace estimation and low-rank "
        "approximation analysis with his EPFL group."),
    "yuji-nakatsukasa": (["eigenvalue algorithms", "randomized low-rank", "rational approximation"],
        "Eigenvalue algorithms; fast randomized methods for linear systems, "
        "eigenproblems, and low-rank approximation."),
    "alex-townsend": (["low-rank theory", "spectral methods", "operator learning"],
        "Why-are-matrices-low-rank theory; continuous analogues; operator learning."),
    "nicholas-higham": (["matrix functions", "mixed precision", "rounding error analysis"],
        "Authority on matrix functions and rounding-error analysis (1961–2024)."),
    "james-demmel": (["LAPACK", "communication-avoiding", "error analysis"],
        "LAPACK lead; communication-avoiding algorithms; 'fast linear algebra is stable'."),
    "laura-grigori": (["communication-avoiding", "randomized orthogonalization", "HPC"],
        "Communication-avoiding LU/QR; randomized Gram–Schmidt and sketched Krylov."),
    "erin-carson": (["mixed precision", "communication-avoiding Krylov"],
        "Mixed-precision iterative refinement; s-step Krylov stability. Co-organizer "
        "of the Banff 2023 workshop."),
    "zdenek-strakos": (["Krylov theory", "finite precision"],
        "Krylov subspace methods theory; finite-precision Lanczos and CG."),
    "jorg-liesen": (["Krylov theory"],
        "Krylov subspace methods theory; monograph with Strakoš."),
    "deanna-needell": (["Kaczmarz", "stochastic iterative methods", "compressed sensing"],
        "Randomized Kaczmarz and stochastic iterative methods."),
    "elizaveta-rebrova": (["random matrices", "iterative sketching"],
        "Random matrix theory and randomized iterative methods."),
    "michal-derezinski": (["determinantal point processes", "sketching", "stochastic optimization"],
        "DPPs in RandNLA; sketched second-order optimization."),
    "haim-avron": (["trace estimation", "sketching", "kernel methods"],
        "Avron–Toledo trace estimation analysis; sketching for kernel methods. "
        "Co-organizer of the ICERM 2026 workshop."),
    "sivan-toledo": (["sparse solvers", "trace estimation"],
        "Sparse direct methods; Avron–Toledo randomized trace estimation."),
    "misha-kilmer": (["tensor decompositions", "inverse problems"],
        "t-product tensor framework; randomized methods for inverse problems."),
    "julianne-chung": (["inverse problems", "hybrid regularization"],
        "Hybrid iterative regularization; randomized methods for inverse problems."),
    "matthias-chung": (["inverse problems", "scientific ML"],
        "Computational inverse problems and learning-based regularization."),
    "valeria-simoncini": (["matrix equations", "Krylov methods"],
        "Matrix equations and Krylov convergence theory. Co-organizer of the "
        "ICERM 2026 workshop."),
    "daniel-szyld": (["Krylov methods", "asynchronous iterations"],
        "Krylov convergence theory (long line with Simoncini); asynchronous methods."),
    "lothar-reichel": (["regularization", "quadrature", "SVD algorithms"],
        "Tikhonov regularization, Gauss quadrature, and IRLBA."),
    "daniela-calvetti": (["Bayesian inverse problems"],
        "Bayesian scientific computing (books with Somersalo)."),
    "erkki-somersalo": (["Bayesian inverse problems"],
        "Bayesian scientific computing (books with Calvetti)."),
    "david-persson": (["randomized trace estimation", "low-rank approximation"],
        "funNyström; randomized trace estimation and low-rank approximation."),
    "ethan-epperly": (["RPCholesky", "randomized low-rank", "trace estimation"],
        "Randomly pivoted Cholesky; XTrace; numerical analysis of randomized methods."),
    "robert-webber": (["randomized algorithms", "Monte Carlo"],
        "Randomized low-rank approximation (RPCholesky, XTrace) and Monte Carlo methods."),
    "rachel-ward": (["stochastic gradient methods", "sampling", "sketching"],
        "Stochastic gradient and sampling methods; importance sampling for regression."),
    "kenneth-clarkson": (["sketching", "input-sparsity algorithms"],
        "Clarkson–Woodruff sketching; foundational sketching algorithms."),
    "vladimir-rokhlin": (["fast multipole", "randomized low-rank origins"],
        "Fast multipole method; the original randomized low-rank approximation "
        "papers with Martinsson, Tygert, and Liberty."),
    "mark-tygert": (["randomized SVD origins"],
        "Early randomized algorithms for matrix approximation (with Rokhlin and "
        "Martinsson)."),
    "jelani-nelson": (["sparse embeddings", "streaming"],
        "OSNAP sparse subspace embeddings; streaming algorithms."),
    "tamas-sarlos": (["subspace embeddings", "fast JL"],
        "The 2006 subspace-embedding paper that unlocked fast randomized regression."),
    "ravindran-kannan": (["sampling algorithms", "spectral methods"],
        "Frieze–Kannan–Vempala sampling; foundational randomized matrix algorithms."),
    "mert-pilanci": (["sketching for optimization"],
        "Sketching for convex optimization; Newton sketch."),
    "riley-murray": (["RandNLA software"],
        "Leads the RandLAPACK / RandBLAS standardization effort."),
    "ming-gu": (["rank-revealing factorizations", "randomized QR"],
        "Rank-revealing and randomized pivoted factorizations; subspace iteration analysis."),
    "edo-liberty": (["frequent directions", "streaming low-rank"],
        "Frequent Directions sketching; early randomized SVD work at Yale."),
    "john-urschel": (["matrix analysis", "Lanczos theory"],
        "Matrix analysis and spectral graph theory; former NFL lineman."),
    "cleve-moler": (["MATLAB", "numerical software"],
        "Creator of MATLAB."),
    "alan-edelman": (["random matrix theory", "Julia"],
        "Random matrix theory; co-creator of Julia."),
    "ioana-dumitriu": (["random matrix theory", "spectral algorithms"],
        "Matrix models for beta-ensembles; randomized spectral algorithms."),
    "nikhil-srivastava": (["free probability", "spectral sparsification", "shifted QR"],
        "Kadison–Singer / interlacing families; pseudospectral shattering and "
        "shifted QR convergence. Co-organizer of the Banff 2023 workshop."),
    "richard-peng": (["Laplacian solvers", "graph algorithms"],
        "Fast Laplacian and structured linear system solvers. Co-organizer of the "
        "Banff 2023 workshop."),
    "rasmus-kyng": (["Laplacian solvers"],
        "Approximate Gaussian elimination for Laplacians; hardness for structured systems."),
    "sushant-sachdeva": (["Laplacian solvers", "optimization"],
        "Laplacian solvers and fast graph algorithms."),
    "santosh-vempala": (["randomized algorithms", "spectral methods"],
        "Randomized and spectral algorithms; solving sparse systems faster than "
        "matrix multiplication (with Peng)."),
    "michael-kapralov": (["streaming", "sketching"],
        "Streaming and sketching algorithms; spectral sparsification."),
    "aaron-sidford": (["optimization", "spectral methods"],
        "Optimization and fast linear system solvers."),
    "ainesh-bakshi": (["sketching", "robust statistics"],
        "Low-rank approximation and robust statistics."),
    "josh-alman": (["matrix multiplication"],
        "Fast matrix multiplication algorithms."),
    "madeleine-udell": (["low-rank models", "optimization"],
        "Generalized low-rank models; practical sketching for optimization."),
    "xiaoye-sherry-li": (["sparse direct solvers"],
        "SuperLU sparse direct solvers; scalable numerical libraries."),
    "edmond-chow": (["preconditioning", "parallel algorithms"],
        "Parallel preconditioning and approximate inverse methods."),
    "shashanka-ubaru": (["trace estimation", "graph ML"],
        "Stochastic Lanczos quadrature for spectrum and trace estimation."),
    "lior-horesh": (["scientific ML", "quantum computing"],
        "Scientific machine learning and quantum algorithms at IBM."),
    "fred-roosta": (["sub-sampled Newton methods"],
        "Sub-sampled and sketched second-order optimization."),
    "robert-gower": (["stochastic optimization", "sketch-and-project"],
        "Sketch-and-project framework; stochastic optimization."),
    "arvind-saibaba": (["randomized inverse problems"],
        "Randomized methods for inverse problems and model reduction. Co-organizer "
        "of the ICERM 2026 workshop."),
    "anna-ma": (["stochastic iterative methods"],
        "Randomized Kaczmarz-type methods. Co-organizer of the ICERM 2026 workshop."),
    "agnieszka-miedlar": (["eigenvalue problems"],
        "Eigenvalue computations; co-organizer of the ICERM 2026 workshop."),
    "jamie-haddock": (["Kaczmarz methods"],
        "Randomized Kaczmarz and iterative projection methods."),
    "heather-wilber": (["rational approximation", "low-rank structure"],
        "Rational approximation and structured low-rank computations."),
    "diana-halikias": (["operator learning", "low-rank recovery"],
        "Matrix recovery from matvec queries; operator learning."),
    "nicolas-boulle": (["operator learning"],
        "Data-efficient operator learning; learning Green's functions."),
    "raphael-meyer": (["trace estimation", "matvec query complexity"],
        "Hutch++ and optimal trace estimation query complexity."),
    "alice-cortinovis": (["trace estimation", "low-rank approximation"],
        "Randomized trace estimation analysis; low-rank approximation."),
    "stefano-massei": (["hierarchical matrices"],
        "Hierarchical / rank-structured matrix computations."),
    "davide-palitta": (["matrix equations"],
        "Matrix equations and large-scale Sylvester/Lyapunov solvers."),
    "eric-de-sturler": (["Krylov recycling"],
        "Krylov subspace recycling; inverse problems."),
    "james-baglama": (["SVD algorithms"],
        "IRLBA: restarted Lanczos bidiagonalization for the partial SVD."),
    "akil-narayan": (["uncertainty quantification", "sampling"],
        "Sampling methods for approximation and UQ."),
    "yijun-dong": (["randomized low-rank", "dimension reduction"],
        "Randomized dimension reduction and low-rank approximation."),
    "jorge-garza-vargas": (["free probability", "spectral algorithms"],
        "Pseudospectral shattering; global convergence of shifted QR."),
    "olga-holtz": (["stability theory", "fast algorithms"],
        "Stability of fast matrix algorithms."),
    "zhaojun-bai": (["eigenvalue problems", "LAPACK"],
        "Large-scale eigenvalue computations; LAPACK and Templates."),
    "david-bindel": (["eigenvalue problems", "kernel methods"],
        "Eigenvalue computations, kernels, and network analysis."),
    "julien-langou": (["LAPACK", "communication-avoiding QR"],
        "Dense linear algebra libraries; CAQR."),
    "stefano-pozza": (["Krylov methods", "matrix functions"],
        "Lanczos-based methods and time-ordered exponentials."),
    "elizabeth-newman": (["tensor methods", "scientific ML"],
        "t-product tensor frameworks for deep learning and imaging."),
    "mirjeta-pasha": (["inverse problems", "regularization"],
        "Computational inverse problems and Bayesian regularization."),
    "taejun-park": (["randomized low-rank"],
        "Randomized low-rank approximation algorithms."),
    "chris-camano": (["randomized tensor methods"],
        "Randomized algorithms for tensor networks and Krylov methods."),
    "noah-amsel": (["matrix functions", "approximation theory"],
        "Near-optimal approximation of matrix functions; Krylov methods."),
    "ryan-schneider": (["eigenvalue problems", "pseudospectra"],
        "Randomized diagonalization; pseudospectral divide-and-conquer."),
    "rikhav-shah": (["random matrices", "eigenvalue algorithms"],
        "Smoothed analysis and randomized eigenvalue computation."),
    "anna-yesypenko": (["fast direct solvers"],
        "Randomized compression and fast direct solvers."),
    "katherine-pearce": (["randomized low-rank"],
        "Randomized interpolative and CUR-type decompositions."),
    "ruhui-jin": (["tensor sketching"],
        "Sketching for tensor problems."),
    "jackie-lok": (["randomized iterative methods"],
        "Randomized Kaczmarz-type and iterative methods."),
    "igor-simunec": (["matrix functions", "Krylov methods"],
        "Krylov methods for matrix functions and network analysis."),
    "theo-mary": (["mixed precision", "probabilistic error analysis"],
        "Probabilistic rounding-error analysis; block low-rank solvers."),
    "ieva-dauzickaite": (["mixed precision", "randomized methods"],
        "Randomized and mixed-precision methods for large linear systems."),
}


def slug(name: str) -> str:
    name = name.translate(str.maketrans({"ł": "l", "Ł": "L", "ø": "o", "Ø": "O"}))
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return s


def canon_person(raw):
    name = CANON_NAME.get(raw["name"], raw["name"])
    aff = CANON_AFF.get(raw["affiliation"], raw["affiliation"])
    return name, aff


def main():
    banff = yaml.safe_load((HERE / "banff_raw.yaml").read_text())["workshops"][0]
    icerm = yaml.safe_load((HERE / "icerm_raw.yaml").read_text())["workshops"][0]

    people = {}  # id -> dict
    rosters = {}  # workshop id -> [person ids]

    # Banff first, then ICERM so the more recent (2026) affiliation wins on overlap.
    for w in (banff, icerm):
        ids = []
        for raw in w["participants"]:
            name, aff = canon_person(raw)
            pid = slug(name)
            people[pid] = {"id": pid, "name": name, "affiliation": aff}
            ids.append(pid)
        rosters[w["id"]] = ids

    for name, aff in ADDED:
        pid = slug(name)
        assert pid not in people, f"'added' person already present: {pid}"
        people[pid] = {"id": pid, "name": name, "affiliation": aff}

    for pid, aff in AFF_OVERRIDE.items():
        assert pid in people, pid
        people[pid]["affiliation"] = aff

    for pid, (topics, notes) in CURATED.items():
        assert pid in people, f"curated topics for unknown person: {pid}"
        people[pid]["topics"] = topics
        people[pid]["notes"] = notes

    # organizers -> ids (Miedlar is an organizer but not on the participant list)
    def org_ids(w):
        out = []
        for n in w["organizers"]:
            pid = slug(CANON_NAME.get(n, n))
            assert pid in people, f"organizer not a known person: {n}"
            out.append(pid)
        return out

    workshops = []
    for w, venue in ((banff, "Banff International Research Station (BIRS 23w5108)"),
                     (icerm, "ICERM, Brown University")):
        workshops.append({
            "id": w["id"],
            "tag": "banff" if w["id"].startswith("banff") else "icerm",
            "title": w["title"],
            "venue": venue,
            "dates": w["dates"],
            "url": w["url"],
            "organizers": org_ids(w),
            "attendees": rosters[w["id"]],
        })

    class Dumper(yaml.SafeDumper):
        pass

    def str_rep(dumper, s):
        if "\n" in s:
            return dumper.represent_scalar("tag:yaml.org,2002:str", s, style="|")
        return dumper.represent_scalar("tag:yaml.org,2002:str", s)

    Dumper.add_representer(str, str_rep)

    def dump(obj, path, header):
        text = yaml.dump(obj, Dumper=Dumper, allow_unicode=True, sort_keys=False,
                         width=88, default_flow_style=False)
        path.write_text(header + text)
        print(f"wrote {path}")

    people_sorted = sorted(people.values(), key=lambda p: p["name"])
    dump(people_sorted, OUT / "people.yaml",
         "# One entry per person. id is referenced by workshops.yaml and\n"
         "# connections.yaml. Keep affiliations written consistently - the\n"
         "# same_institution factor is computed by exact (case-insensitive) match.\n"
         "# Optional keys: website, topics (list), notes.\n")
    dump(workshops, OUT / "workshops.yaml",
         "# Workshops with their attendee rosters (provenance for the graph).\n"
         "# tag: groups workshops for the node-group rules in config.yaml.\n"
         "# attendees/organizers reference ids from people.yaml.\n")
    print(f"{len(people_sorted)} people, "
          f"{sum(len(r) for r in rosters.values())} attendances")


if __name__ == "__main__":
    main()
