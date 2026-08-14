"""Welke klas hoort bij een lopende huur.

`toewijzingen.leerling_klas` is een momentopname van het moment van uitgifte en
kantelt niet mee met de jaarwisseling: op 1 augustus zet Magister iedereen een
leerjaar hoger, maar dat veld blijft staan. Groeperen of filteren op dat veld
laat de brugklas van vorig jaar doorlopen in die van dit jaar. Op CT101 gaf
HV1D daardoor 49 regels voor een klas van 24, en leerlingen met een oude
momentopname (Talisha Kolthof, Tekmile Bahar, Irem Çag) vielen juist helemaal
buiten hun eigen klas.

Daarom wint de actuele klas uit `leerlingen`. Het vastgelegde veld is de
terugval, en dat is geen detail: installaties zonder Magister-sync (Hengelo)
hebben een lege leerlingentabel, en huurders zonder stamnummer hebben nergens
een leerlingrij. Voor allebei is de momentopname het enige dat er is.

De momentopname blijft ongemoeid op de toewijzing staan. Die vertelt nog steeds
in welke klas iemand zat toen hij het kluisje kreeg, en dat is precies wat je
van een historische registratie wil.

Gebruik: de query moet `toewijzingen t` en een LEFT JOIN op `leerlingen l` in
scope hebben.
"""

KLAS_SQL = "COALESCE(NULLIF(TRIM(l.klas), ''), NULLIF(TRIM(t.leerling_klas), ''))"
