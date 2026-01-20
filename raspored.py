import random
import sys

# Povećan limit rekurzije za svaki slučaj
sys.setrecursionlimit(3000)

# ==========================================
# 1. DEFINICIJA ENTITETA
# ==========================================

class Nastavnik:
    def __init__(self, ime):
        self.ime = ime
    def __repr__(self): return self.ime

class Razred:
    def __init__(self, oznaka):
        self.oznaka = oznaka
    def __repr__(self): return self.oznaka

class BlokPredmet:
    """
    Predstavlja blok sat (2 školska sata odjednom).
    """
    def __init__(self, naziv, nastavnik, razred):
        self.naziv = naziv
        self.nastavnik = nastavnik
        self.razred = razred
    def __repr__(self): return f"{self.naziv} (Blok)"

class Ucionica:
    def __init__(self, naziv):
        self.naziv = naziv
    def __repr__(self): return self.naziv

class TerminBloka:
    """
    Definira fiksne termine blokova prema tvojim pravilima vremena.
    """
    def __init__(self, dan, indeks, vrijeme_opis):
        self.dan = dan
        self.indeks = indeks # 0, 1, 2, 3
        self.vrijeme_opis = vrijeme_opis # npr. "08:00 - 09:35"
    
    def __repr__(self): return f"{self.dan} {self.vrijeme_opis}"

# ==========================================
# 2. PROVJERA KONFLIKTA (CSPs)
# ==========================================

def provjeri_konflikt(raspored, novi_termin, novi_nastavnik, nova_ucionica, novi_razred):
    """
    Provjerava krši li novi blok pravila fizike (jedna osoba na dva mjesta).
    """
    for (predmet, termin, ucionica) in raspored:
        # Gledamo samo ako je isti dan i isti termin bloka
        if termin.dan == novi_termin.dan and termin.indeks == novi_termin.indeks:
            
            # 1. Učionica zauzeta?
            if ucionica == nova_ucionica: return True
            
            # 2. Nastavnik zauzet?
            if predmet.nastavnik == novi_nastavnik: return True
            
            # 3. Razred već ima nastavu?
            if predmet.razred == novi_razred: return True
            
    return False

# ==========================================
# 3. ALGORITAM PRETRAŽIVANJA (Backtracking)
# ==========================================

def generiraj_raspored(preostali_blokovi, svi_termini, sve_ucionice, trenutni_raspored):
    # Ako nema više blokova, gotovi smo!
    if not preostali_blokovi:
        return trenutni_raspored

    # Uzimamo sljedeći blok za rasporediti
    trenutni_blok = preostali_blokovi[0]
    
    # Heuristika: Randomizacija termina smanjuje šansu da se algoritam "zaglavi"
    # i osigurava da predmeti nisu uvijek u isto doba dana.
    termini_random = svi_termini[:]
    random.shuffle(termini_random)
    
    for termin in termini_random:
        for ucionica in sve_ucionice:
            
            if not provjeri_konflikt(trenutni_raspored, termin, 
                                     trenutni_blok.nastavnik, 
                                     ucionica, 
                                     trenutni_blok.razred):
                
                # Dodajemo u raspored
                novi_unos = (trenutni_blok, termin, ucionica)
                
                # Rekurzija
                rezultat = generiraj_raspored(
                    preostali_blokovi[1:], 
                    svi_termini, 
                    sve_ucionice, 
                    trenutni_raspored + [novi_unos]
                )
                
                if rezultat is not None:
                    return rezultat
                
                # Backtracking (poništi i probaj dalje)
    
    return None

# ==========================================
# 4. PRIPREMA PODATAKA (Realni scenarij)
# ==========================================

# --- Nastavnici ---
n_mat = Nastavnik("Prof. Horvat (Mat)") # Strogi profesor
n_hrv = Nastavnik("Prof. Kovač (Hrv)")
n_eng = Nastavnik("Prof. Smith (Eng)")
n_inf = Nastavnik("Prof. Jurić (Inf)")
n_priroda = Nastavnik("Prof. Babić (Fiz/Bio)") # Predaje više predmeta
n_drustvo = Nastavnik("Prof. Zec (Pov/Geo)")

# --- Učionice ---
ucionice = [
    Ucionica("Učionica 1 (Velika)"), 
    Ucionica("Učionica 2 (Manja)"), 
    Ucionica("Informatička")
]

# --- Razredi ---
r1a = Razred("1.A")
r1b = Razred("1.B")

# --- Generiranje Blokova (Kurikulum) ---
# Tjedno opterećenje: cca 12-14 blokova (24-28 školskih sati)
blokovi_za_rasporediti = []

def dodaj_predmet(razred, naziv, nastavnik, broj_blokova_tjedno):
    for _ in range(broj_blokova_tjedno):
        blokovi_za_rasporediti.append(BlokPredmet(naziv, nastavnik, razred))

# Kurikulum za 1.A
dodaj_predmet(r1a, "Matematika", n_mat, 3)     # 3 bloka = 6 sati
dodaj_predmet(r1a, "Hrvatski", n_hrv, 3)       # 3 bloka = 6 sati
dodaj_predmet(r1a, "Engleski", n_eng, 2)       # 2 bloka = 4 sata
dodaj_predmet(r1a, "Informatika", n_inf, 2)    # 2 bloka = 4 sata
dodaj_predmet(r1a, "Fizika", n_priroda, 1)     # 1 blok = 2 sata
dodaj_predmet(r1a, "Biologija", n_priroda, 1)  # 1 blok = 2 sata
dodaj_predmet(r1a, "Povijest", n_drustvo, 1)   # 1 blok = 2 sata

# Kurikulum za 1.B
dodaj_predmet(r1b, "Matematika", n_mat, 3)
dodaj_predmet(r1b, "Hrvatski", n_hrv, 3)
dodaj_predmet(r1b, "Engleski", n_eng, 2)
dodaj_predmet(r1b, "Informatika", n_inf, 2)
dodaj_predmet(r1b, "Fizika", n_priroda, 1)
dodaj_predmet(r1b, "Biologija", n_priroda, 1)
dodaj_predmet(r1b, "Povijest", n_drustvo, 1)

# Važno: Promiješati blokove da ne budu svi iste vrste zaredom
random.seed(101) # Fiksni seed za ponovljivost (probaj mijenjati broj ako želiš drugačiji raspored)
random.shuffle(blokovi_za_rasporediti)

# --- Generiranje Vremenskih Termina ---
# 1. sat: 8:00-8:45, pauza 5, 2. sat: 8:50-9:35 -> BLOK 1: 08:00 - 09:35
# 3. sat: 9:40-10:25, pauza 5, 4. sat: 10:30-11:15 -> BLOK 2: 09:40 - 11:15
# 5. sat: 11:20-12:05, pauza 5, 6. sat: 12:10-12:55 -> BLOK 3: 11:20 - 12:55
# 7. sat: 13:00-13:45, pauza 5, 8. sat: 13:50-14:35 -> BLOK 4: 13:00 - 14:35

dani = ["PONEDJELJAK", "UTORAK", "SRIJEDA", "ČETVRTAK", "PETAK"]
vremena = [
    (0, "08:00 - 09:35 (1. blok)"),
    (1, "09:40 - 11:15 (2. blok)"),
    (2, "11:20 - 12:55 (3. blok)"),
    (3, "13:00 - 14:35 (4. blok)")
]

svi_termini = []
for dan in dani:
    for indeks, opis in vremena:
        svi_termini.append(TerminBloka(dan, indeks, opis))

# ==========================================
# 5. IZVRŠAVANJE I ISPIS
# ==========================================

print(f"Pokušavam rasporediti {len(blokovi_za_rasporediti)} blok-sati (ukupno {len(blokovi_za_rasporediti)*2} školskih sati)...")
print("Tražim optimalno rješenje...\n")

konacni_raspored = generiraj_raspored(blokovi_za_rasporediti, svi_termini, ucionice, [])

if konacni_raspored:
    # Sortiranje: Dan -> Termin -> Razred
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
    print("Nastava završava najkasnije u 14:35.")
else:
    print("Greška: Nemoguće napraviti raspored s ovim ograničenjima. Probaj dodati još jednu učionicu.")