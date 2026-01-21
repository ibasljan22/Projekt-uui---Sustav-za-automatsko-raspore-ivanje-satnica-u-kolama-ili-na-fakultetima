import random
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional
import math

# ==========================================
# 1) ENTITETI
# ==========================================

class Nastavnik:
    def __init__(self, ime: str):
        self.ime = ime
    def __repr__(self): return self.ime

class Razred:
    def __init__(self, oznaka: str):
        self.oznaka = oznaka
    def __repr__(self): return self.oznaka

class BlokPredmet:
    """Predstavlja blok sat (2 školska sata odjednom)."""
    def __init__(self, naziv: str, nastavnik: Nastavnik, razred: Razred):
        self.naziv = naziv
        self.nastavnik = nastavnik
        self.razred = razred
    def __repr__(self): return f"{self.naziv} (Blok)"

class Ucionica:
    def __init__(self, naziv: str):
        self.naziv = naziv
    def __repr__(self): return self.naziv

class TerminBloka:
    """Definira fiksne termine blokova."""
    def __init__(self, dan: str, day_idx: int, indeks: int, vrijeme_opis: str):
        self.dan = dan
        self.day_idx = day_idx     # 0..4
        self.indeks = indeks       # 0..3
        self.vrijeme_opis = vrijeme_opis
    def __repr__(self): return f"{self.dan} {self.vrijeme_opis}"

# ==========================================
# 2) TIPOVI
# ==========================================

RasporedUnos = Tuple[BlokPredmet, TerminBloka, Ucionica]
Dodjela = Tuple[TerminBloka, Ucionica]

# ==========================================
# 3) BRZA PROVJERA KONFLIKTA (set-ovi)
# ==========================================

def konflikt_sets(teacher_busy, class_busy, room_busy, blok: BlokPredmet, termin: TerminBloka, ucionica: Ucionica) -> bool:
    key = (termin.day_idx, termin.indeks)
    if (blok.nastavnik, key) in teacher_busy:
        return True
    if (blok.razred, key) in class_busy:
        return True
    if (ucionica, key) in room_busy:
        return True
    return False

# ==========================================
# 4) CSP DOMENE + HEURISTIKE (MRV, LCV, Forward checking)
# ==========================================

def moguce_dodjele(
    blok: BlokPredmet,
    svi_termini: List[TerminBloka],
    sve_ucionice: List[Ucionica],
    teacher_busy,
    class_busy,
    room_busy
) -> List[Dodjela]:
    dom: List[Dodjela] = []
    for t in svi_termini:
        for u in sve_ucionice:
            if not konflikt_sets(teacher_busy, class_busy, room_busy, blok, t, u):
                dom.append((t, u))
    return dom

def odaberi_varijablu_MRV(
    preostali: List[BlokPredmet],
    svi_termini: List[TerminBloka],
    sve_ucionice: List[Ucionica],
    teacher_busy,
    class_busy,
    room_busy
) -> Tuple[BlokPredmet, List[Dodjela]]:
    """
    MRV: izaberi blok s najmanje opcija.
    """
    best_blok = None
    best_dom = None
    best_len = 10**9

    for b in preostali:
        dom = moguce_dodjele(b, svi_termini, sve_ucionice, teacher_busy, class_busy, room_busy)
        if len(dom) < best_len:
            best_len = len(dom)
            best_blok = b
            best_dom = dom
            if best_len == 0:
                break

    return best_blok, best_dom  # type: ignore

def forward_check(
    preostali: List[BlokPredmet],
    svi_termini: List[TerminBloka],
    sve_ucionice: List[Ucionica],
    teacher_busy,
    class_busy,
    room_busy
) -> bool:
    """
    Forward checking: svaki preostali blok mora imati barem 1 opciju.
    """
    for b in preostali:
        if len(moguce_dodjele(b, svi_termini, sve_ucionice, teacher_busy, class_busy, room_busy)) == 0:
            return False
    return True

def lcv_score(
    blok: BlokPredmet,
    dodjela: Dodjela,
    preostali: List[BlokPredmet],
    svi_termini: List[TerminBloka],
    sve_ucionice: List[Ucionica],
    teacher_busy,
    class_busy,
    room_busy
) -> int:
    """
    LCV: koliko opcija ostaje drugima nakon što privremeno dodijelimo ovu vrijednost.
    Veće je bolje.
    """
    t, u = dodjela

    # privremeno zauzmi
    key = (t.day_idx, t.indeks)

    teacher_busy2 = set(teacher_busy); teacher_busy2.add((blok.nastavnik, key))
    class_busy2 = set(class_busy);     class_busy2.add((blok.razred, key))
    room_busy2 = set(room_busy);       room_busy2.add((u, key))

    total = 0
    for other in preostali:
        if other is blok:
            continue
        total += len(moguce_dodjele(other, svi_termini, sve_ucionice, teacher_busy2, class_busy2, room_busy2))
    return total

# ==========================================
# 5) OPTIMALNOST: COST FUNKCIJA (ravnomjerna raspodjela po danima)
# ==========================================

def make_class_totals(blokovi: List[BlokPredmet]) -> Dict[Razred, int]:
    totals: Dict[Razred, int] = {}
    for b in blokovi:
        totals[b.razred] = totals.get(b.razred, 0) + 1
    return totals

def incremental_balance_cost(
    razred: Razred,
    day_idx: int,
    counts_by_class_day: Dict[Razred, List[int]],
    ideal_per_day: Dict[Razred, float],
    w_balance: float
) -> float:
    """
    Trošak ravnomjernosti: sum_{day} (count(day) - ideal)^2
    Incremental = razlika kad povećamo count na tom danu za 1.
    """
    old = counts_by_class_day[razred][day_idx]
    new = old + 1
    ideal = ideal_per_day[razred]
    before = (old - ideal) ** 2
    after = (new - ideal) ** 2
    return w_balance * (after - before)

# ==========================================
# 6) DFS IZ LABOSA + BRANCH & BOUND (optimalno)
# ==========================================

@dataclass
class Node:
    raspored: List[RasporedUnos]
    preostali: List[BlokPredmet]
    teacher_busy: set
    class_busy: set
    room_busy: set
    counts_by_class_day: Dict[Razred, List[int]]
    cost_so_far: float

def dfs_csp_optimal_schedule(
    blokovi: List[BlokPredmet],
    svi_termini: List[TerminBloka],
    sve_ucionice: List[Ucionica],
    max_nodes: int = 2_000_000,
    seed: int = 101,
    w_balance: float = 6.0,       # koliko jako forsira ravnomjernost kroz dane
    progress_every: int = 20000
) -> Optional[List[RasporedUnos]]:
    """
    DFS (iterativno sa stogom) + MRV + LCV + forward checking
    + Branch & Bound nad cost funkcijom (traži optimalan raspored).
    """
    random.seed(seed)

    # ideal po danu za svaki razred
    totals = make_class_totals(blokovi)
    ideal_per_day = {r: totals[r] / 5.0 for r in totals}  # 5 radnih dana

    # inicijalno brojanje po razred/dan
    counts_by_class_day0 = {r: [0, 0, 0, 0, 0] for r in totals}

    start = Node(
        raspored=[],
        preostali=list(blokovi),
        teacher_busy=set(),
        class_busy=set(),
        room_busy=set(),
        counts_by_class_day=counts_by_class_day0,
        cost_so_far=0.0
    )

    best_cost = float("inf")
    best_solution: Optional[List[RasporedUnos]] = None

    stack: List[Node] = [start]
    visited = 0

    while stack and visited < max_nodes:
        node = stack.pop()
        visited += 1

        if progress_every and visited % progress_every == 0:
            print(f"[DFS-opt] visited={visited}, best_cost={best_cost:.3f}, depth={len(node.raspored)}/{len(blokovi)}, stack={len(stack)}")

        # Ako smo već gori od najboljeg, nema smisla
        if node.cost_so_far >= best_cost:
            continue

        # cilj
        if not node.preostali:
            # potpuno rješenje
            if node.cost_so_far < best_cost:
                best_cost = node.cost_so_far
                best_solution = node.raspored
            continue

        # MRV: izaberi najteži blok
        blok, dom = odaberi_varijablu_MRV(
            node.preostali, svi_termini, sve_ucionice,
            node.teacher_busy, node.class_busy, node.room_busy
        )
        if dom is None or len(dom) == 0:
            continue

        # Pripremi domenu s rangiranjem:
        # 1) minimalni inkrement troška (ravnomjernost)
        # 2) LCV (više opcija ostalima = bolje)
        scored_values = []
        for d in dom:
            t, u = d
            inc = incremental_balance_cost(
                razred=blok.razred,
                day_idx=t.day_idx,
                counts_by_class_day=node.counts_by_class_day,
                ideal_per_day=ideal_per_day,
                w_balance=w_balance
            )
            lcv = lcv_score(
                blok=blok,
                dodjela=d,
                preostali=node.preostali,
                svi_termini=svi_termini,
                sve_ucionice=sve_ucionice,
                teacher_busy=node.teacher_busy,
                class_busy=node.class_busy,
                room_busy=node.room_busy
            )
            # sortiramo: manji inc bolje, veći lcv bolje
            scored_values.append((inc, -lcv, d))

        scored_values.sort(key=lambda x: (x[0], x[1]))

        # DFS: push obrnuto da se prvo isproba najbolja opcija
        for inc, _neg_lcv, (t, u) in reversed(scored_values):
            key = (t.day_idx, t.indeks)

            # napravi nove setove
            teacher_busy2 = set(node.teacher_busy); teacher_busy2.add((blok.nastavnik, key))
            class_busy2 = set(node.class_busy);     class_busy2.add((blok.razred, key))
            room_busy2 = set(node.room_busy);       room_busy2.add((u, key))

            # ažuriraj counts_by_class_day (kopiraj samo listu za taj razred)
            counts2 = dict(node.counts_by_class_day)
            counts2[blok.razred] = counts2[blok.razred].copy()
            counts2[blok.razred][t.day_idx] += 1

            cost2 = node.cost_so_far + inc

            # Branch & Bound pruning
            if cost2 >= best_cost:
                continue

            preostali2 = [b for b in node.preostali if b is not blok]
            raspored2 = node.raspored + [(blok, t, u)]

            # Forward checking (brzo rezanje)
            if not forward_check(preostali2, svi_termini, sve_ucionice, teacher_busy2, class_busy2, room_busy2):
                continue

            stack.append(Node(
                raspored=raspored2,
                preostali=preostali2,
                teacher_busy=teacher_busy2,
                class_busy=class_busy2,
                room_busy=room_busy2,
                counts_by_class_day=counts2,
                cost_so_far=cost2
            ))

    if best_solution is not None:
        print(f"[DFS-opt] Optimalno rješenje nađeno. visited={visited}, best_cost={best_cost:.3f}")
    else:
        print(f"[DFS-opt] Nije nađeno rješenje u limitu čvorova. visited={visited}, max_nodes={max_nodes}")
    return best_solution

# ==========================================
# 7) ISPIS
# ==========================================

def ispisi_raspored(konacni_raspored: List[RasporedUnos], dani: List[str]) -> None:
    dan_map = {d: i for i, d in enumerate(dani)}
    konacni_raspored.sort(key=lambda x: (dan_map[x[1].dan], x[1].indeks, x[0].razred.oznaka))

    current_day = ""
    print("=" * 110)
    print(f"{'VRIJEME':<25} | {'RAZRED':<6} | {'PREDMET (2 SATA)':<18} | {'NASTAVNIK':<25} | {'UČIONICA'}")
    print("=" * 110)

    for (predmet, termin, ucionica) in konacni_raspored:
        if termin.dan != current_day:
            print(f"\n>>> {termin.dan} <<<")
            print("-" * 110)
            current_day = termin.dan

        print(f"{termin.vrijeme_opis:<25} | {str(predmet.razred):<6} | {predmet.naziv:<18} | {str(predmet.nastavnik):<25} | {ucionica.naziv}")

    print("\n" + "=" * 110)
    print("NAPOMENA: Svi prikazani predmeti traju 2 školska sata (90 min + pauze).")
    print("Dan može završiti ranije ako nema više blokova za taj razred (što je dozvoljeno).")

# ==========================================
# 8) PODACI (tvoji)
# ==========================================

# --- Nastavnici ---
n_mat = Nastavnik("Prof. Horvat (Mat)")
n_hrv = Nastavnik("Prof. Kovač (Hrv)")
n_eng = Nastavnik("Prof. Smith (Eng)")
n_inf = Nastavnik("Prof. Jurić (Inf)")
n_priroda = Nastavnik("Prof. Babić (Fiz/Bio)")
n_drustvo = Nastavnik("Prof. Zec (Pov/Geo)")
n_lik = Nastavnik("Prof. Barišić (Lik)")
n_glaz = Nastavnik("Prof. Novak (Glaz)")
n_tech = Nastavnik("Prof. Marić (Teh)")
n_raz = Nastavnik("Razrednik (SR)")

# --- Učionice ---
ucionice = [
    Ucionica("Učionica 1 (Velika)"),
    Ucionica("Učionica 2 (Manja)"),
    Ucionica("Informatička")
]

# --- Razredi ---
r1a = Razred("1.A")
r1b = Razred("1.B")

# --- Blokovi ---
blokovi_za_rasporediti: List[BlokPredmet] = []

def dodaj_predmet(razred: Razred, naziv: str, nastavnik: Nastavnik, broj_blokova_tjedno: int):
    for _ in range(broj_blokova_tjedno):
        blokovi_za_rasporediti.append(BlokPredmet(naziv, nastavnik, razred))

# 1.A
dodaj_predmet(r1a, "Matematika", n_mat, 3)
dodaj_predmet(r1a, "Hrvatski", n_hrv, 3)
dodaj_predmet(r1a, "Engleski", n_eng, 2)
dodaj_predmet(r1a, "Informatika", n_inf, 2)
dodaj_predmet(r1a, "Fizika", n_priroda, 1)
dodaj_predmet(r1a, "Biologija", n_priroda, 1)
dodaj_predmet(r1a, "Povijest", n_drustvo, 1)
dodaj_predmet(r1a, "Likovni", n_lik, 1)
dodaj_predmet(r1a, "Glazbeni", n_glaz, 1)
dodaj_predmet(r1a, "Tehnička", n_tech, 1)
dodaj_predmet(r1a, "Sat razrednika", n_raz, 1)

# 1.B
dodaj_predmet(r1b, "Matematika", n_mat, 3)
dodaj_predmet(r1b, "Hrvatski", n_hrv, 3)
dodaj_predmet(r1b, "Engleski", n_eng, 2)
dodaj_predmet(r1b, "Informatika", n_inf, 2)
dodaj_predmet(r1b, "Fizika", n_priroda, 1)
dodaj_predmet(r1b, "Biologija", n_priroda, 1)
dodaj_predmet(r1b, "Povijest", n_drustvo, 1)
dodaj_predmet(r1b, "Likovni", n_lik, 1)
dodaj_predmet(r1b, "Glazbeni", n_glaz, 1)
dodaj_predmet(r1b, "Tehnička", n_tech, 1)
dodaj_predmet(r1b, "Sat razrednika", n_raz, 1)

# promiješaj (DFS će svejedno MRV-om birati teško prvo)
random.seed(101)
random.shuffle(blokovi_za_rasporediti)

# --- Termini blokova (4 bloka dnevno x 5 dana) ---
dani = ["PONEDJELJAK", "UTORAK", "SRIJEDA", "ČETVRTAK", "PETAK"]
vremena = [
    (0, "08:00 - 09:35 (1. blok)"),
    (1, "09:40 - 11:15 (2. blok)"),
    (2, "11:20 - 12:55 (3. blok)"),
    (3, "13:00 - 14:35 (4. blok)")
]

svi_termini: List[TerminBloka] = []
for day_idx, dan in enumerate(dani):
    for indeks, opis in vremena:
        svi_termini.append(TerminBloka(dan, day_idx, indeks, opis))

# ==========================================
# 9) IZVRŠAVANJE
# ==========================================

print(f"Pokušavam rasporediti {len(blokovi_za_rasporediti)} blok-sati (ukupno {len(blokovi_za_rasporediti)*2} školskih sati)...")
print("Tražim optimalno rješenje: DFS (labos) + MRV + LCV + forward checking + Branch&Bound(cost=ravnomjernost)\n")

konacni_raspored = dfs_csp_optimal_schedule(
    blokovi=blokovi_za_rasporediti,
    svi_termini=svi_termini,
    sve_ucionice=ucionice,
    max_nodes=2_000_000,
    seed=101,
    w_balance=6.0,        
    progress_every=20000
)

if konacni_raspored:
    ispisi_raspored(konacni_raspored, dani)
else:
    print("Greška: Nemoguće napraviti raspored s ovim ograničenjima (ili je limit max_nodes premalen).")
    print("Probaj povećati max_nodes ili dodati još jednu učionicu.")
