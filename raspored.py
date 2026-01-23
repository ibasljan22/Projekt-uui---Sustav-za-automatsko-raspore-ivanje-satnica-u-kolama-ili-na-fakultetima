#PODACI
razredi = ["3b", "4c", "6b", "8a"]

predmeti_po_razredu = {
    "3b": ["mat", "hrv", "lik", "prir", "glaz", "tjelesni", "SRZ"],
    "4c": ["mat", "hrv", "lik", "prir", "glaz", "tjelesni", "SRZ"],
    "6b": ["mat", "hrv", "geo", "fiz", "inf", "tjelesni", "SRZ", "pov", "kem"],
    "8a": ["mat", "hrv", "geo", "fiz", "inf", "tjelesni", "SRZ", "pov", "kem"],
}

sati_po_predmetu = {
    "mat": 4, "hrv": 4, "lik": 2, "prir": 3, "geo": 2,
    "glaz": 1, "fiz": 2, "inf": 1, "tjelesni": 2,
    "SRZ": 1, "pov": 2, "kem": 2,
}

profesori_za_predmet = {
    "mat": ["prof1", "prof2", "prof3", "prof4", "prof8"],
    "hrv": ["prof1", "prof2", "prof3", "prof4", "prof8"],
    "lik": ["prof1", "prof2", "prof7"],
    "prir": ["prof1", "prof2"],
    "glaz": ["prof1", "prof2", "prof7"],
    "geo": ["prof3", "prof4", "prof6"],
    "fiz": ["prof3", "prof4", "prof6"],
    "inf": ["prof5"],
    "tjelesni": ["prof9", "prof10"],
    "SRZ": ["prof1", "prof2"],
    "pov": ["prof3", "prof4", "prof6"],
    "kem": ["prof2", "prof6"],
}

dani = ["PON", "UTO", "SRI", "CET", "PET"]
termini = [f"{dan}_{sat}" for dan in dani for sat in range(1, 7)]
ucionice = [f"U{i}" for i in range(1, 6)]


#VARIJABLE I DOMENE
varijable = []
for r in razredi:
    for p in predmeti_po_razredu[r]:
        for i in range(sati_po_predmetu[p]):
            varijable.append((r, p, i))

domene = {}
for v in varijable:
    _, predmet, _ = v
    domene[v] = [
        (t, u, prof)
        for t in termini
        for u in ucionice
        for prof in profesori_za_predmet[predmet]
    ]


#ZAUZETOSTI
zauzet_razred = set()
zauzet_profesor = set()
zauzeta_ucionica = set()


#HARD OGRANIČENJA
def provjeri_max_sati_po_danu(rjesenje, razred, termin):
    dan, _ = termin.split("_")
    broj = sum(
        1 for (r, _, _), (t, _, _) in rjesenje.items()
        if r == razred and t.split("_")[0] == dan
    )
    return broj + 1 <= 6

def provjeri_predmet_po_danu(rjesenje, razred, predmet, termin):
    dan, sat = termin.split("_")
    sat = int(sat)

    sati = []
    for (r, p, _), (t, _, _) in rjesenje.items():
        if r == razred and p == predmet:
            d, s = t.split("_")
            if d == dan:
                sati.append(int(s))

    if predmet not in ["mat", "hrv", "tjelesni"]:
        return len(sati) == 0

    if predmet in ["mat", "hrv"]:
        return len(sati) < 2

    if predmet == "tjelesni":
        novi = sorted(sati + [sat])
        if len(novi) > 2:
            return False
        if len(novi) == 2:
            return novi[1] - novi[0] == 1
        return True

    return True

def provjeri_ne_dan_za_danom(rjesenje, razred, predmet, termin):
    if predmet == "tjelesni" or sati_po_predmetu[predmet] >= 3:
        return True

    dan, _ = termin.split("_")
    idx = dani.index(dan)

    for (r, p, _), (t, _, _) in rjesenje.items():
        if r == razred and p == predmet:
            d, _ = t.split("_")
            if abs(idx - dani.index(d)) == 1:
                return False
    return True

def konzistentno(var, vrijednost):
    razred, predmet, _ = var
    termin, ucionica, profesor = vrijednost

    if not provjeri_max_sati_po_danu(rjesenje, razred, termin):
        return False
    if not provjeri_predmet_po_danu(rjesenje, razred, predmet, termin):
        return False
    if not provjeri_ne_dan_za_danom(rjesenje, razred, predmet, termin):
        return False

    for (r, p, _), (_, _, prof) in rjesenje.items():
        if r == razred and p == predmet and prof != profesor:
            return False

    if (razred, termin) in zauzet_razred:
        return False
    if (ucionica, termin) in zauzeta_ucionica:
        return False
    if (profesor, termin) in zauzet_profesor:
        return False

    return True

#SOFT OGRANIČENJA
def kazna_rasporeda(rjesenje):
    kazna = 0

    for razred in razredi:
        sati_po_danu = {dan: [] for dan in dani}

        for (r, _, _), (t, _, _) in rjesenje.items():
            if r == razred:
                dan, sat = t.split("_")
                sati_po_danu[dan].append(int(sat))

        for dan, sati in sati_po_danu.items():
            if not sati:
                kazna += 5
                continue

            sati.sort()
            for i in range(len(sati) - 1):
                if sati[i+1] - sati[i] > 1:
                    kazna += sati[i+1] - sati[i] - 1

    return kazna

#MRV
def odaberi_varijablu(nerasp, domene):
    return min(nerasp, key=lambda v: len(domene[v]))


#FORWARD CHECKING
def forward_checking(var, vrijednost, domene):
    razred, predmet, _ = var
    termin, ucionica, profesor = vrijednost
    uklonjeno = []

    for v in domene:
        if v == var:
            continue

        nova = []
        for (t, u, p) in domene[v]:
            if (
                (v[0] == razred and t == termin) or
                (u == ucionica and t == termin) or
                (p == profesor and t == termin)
            ):
                continue

            if v[0] == razred and v[1] == predmet and p != profesor:
                continue

            nova.append((t, u, p))

        if len(nova) < len(domene[v]):
            uklonjeno.append((v, domene[v]))
            domene[v] = nova

        if not domene[v]:
            return False, uklonjeno

    return True, uklonjeno


#BACKTRACKING
MAX_CVOROVA = 15_000

najbolje_rjesenje = None
najbolja_kazna = float("inf")
broj_cvorova = 0

def backtracking(rjesenje, domene):
    global najbolje_rjesenje, najbolja_kazna, broj_cvorova

    broj_cvorova += 1
    if broj_cvorova >= MAX_CVOROVA:
        return True

    if len(rjesenje) == len(varijable):
        k = kazna_rasporeda(rjesenje)
        print(f"NAĐENO RJEŠENJE – kazna = {k}")

        if k < najbolja_kazna:
            najbolja_kazna = k
            najbolje_rjesenje = rjesenje.copy()
            print(f"NOVO NAJBOLJE RJEŠENJE! Kazna = {k}")
        return False

    nerasp = [v for v in varijable if v not in rjesenje]
    var = odaberi_varijablu(nerasp, domene)

    for vrijednost in domene[var]:
        if konzistentno(var, vrijednost):
            razred, _, _ = var
            termin, ucionica, profesor = vrijednost

            rjesenje[var] = vrijednost
            zauzet_razred.add((razred, termin))
            zauzeta_ucionica.add((ucionica, termin))
            zauzet_profesor.add((profesor, termin))

            uspjeh, uklonjeno = forward_checking(var, vrijednost, domene)
            if uspjeh:
                if backtracking(rjesenje, domene):
                    return True

            del rjesenje[var]
            zauzet_razred.remove((razred, termin))
            zauzeta_ucionica.remove((ucionica, termin))
            zauzet_profesor.remove((profesor, termin))
            for v, stara in uklonjeno:
                domene[v] = stara

    return False

#ISPIS
def ispisi_satnicu_po_razredima(rjesenje, razredi):
    sati = range(1, 7)
    for razred in razredi:
        print("\n" + "=" * 90)
        print(f"SATNICA ZA RAZRED {razred}".center(90))
        print("=" * 90)

        tablica = {dan: {sat: "" for sat in sati} for dan in dani}

        for (r, predmet, _), (termin, ucionica, _) in rjesenje.items():
            if r == razred:
                dan, sat = termin.split("_")
                tablica[dan][int(sat)] = f"{predmet.upper()} ({ucionica})"

        for sat in sati:
            print(f"{sat:<3}", end="")
            for dan in dani:
                print(f"| {tablica[dan][sat]:^14}", end="")
            print("|")

#POKRETANJE
print("POČINJEM PRETRAGU...")
rjesenje = {}
backtracking(rjesenje, domene)

print("\nGOTOVO")
print("Obrađeno čvorova:", broj_cvorova)
print("Najbolja kazna:", najbolja_kazna)

if najbolje_rjesenje:
    ispisi_satnicu_po_razredima(najbolje_rjesenje, razredi)
else:
    print("NEMA RJEŠENJA")
