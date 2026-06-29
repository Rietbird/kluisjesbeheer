-- =====================================================================
-- DD-lijst: sql-get-kluisjes-voorinschrijving
-- =====================================================================
-- Doel    : leerlingen die voor het KOMENDE schooljaar zijn geplaatst,
--           voor de kluisjes-voorinschrijving. In de app KLASLOOS
--           importeren; Klas + Email staan er alleen ter controle in.
-- Filter  : peildatum 1 sept van het komende schooljaar - zelfde
--           dBegin/dEinde/dVertrek-logica als sql-get-isk-leerlingen,
--           maar met een TOEKOMSTIGE peildatum i.p.v. GETDATE().
-- Auteur  : Vincent + Claude, 2026-06-26
-- Status  : * SQL geverifieerd in Decibel (F9 geeft volgend-jaars rijen,
--             o.a. PrO-klassen 456*/F3L45 met locatie "HET ERASMUS
--             vestiging PrO").
--           * Controle-telling: Magister Desktop "Actieve leerlingen 2026-2027"
--             op peildatum 01-08-2026 = 436 totaal (waarvan 239 MAVO/HAVO/VWO).
--             Deze lijst zonder vestiging-filter hoort ~436 rijen te geven.
--           * Webservice (Data.GetData) + account-koppeling: nog te testen.
-- Account : Erasmus-kluisjesapp gebruikt vermoedelijk webservice-user
--           `webuser` (heeft al kluisjes-actueel/zoek-kluiscode) - nog te
--           bevestigen op CT101. Hengelo gebruikt `Kluisjesmodule`.
-- Aanroep : GET <url>/?library=Data&function=GetData
--                 &Layout=sql-get-kluisjes-voorinschrijving
--                 &SessionToken=<token>&Type=XML
--           (DD-lijsten gaan via library=Data, NIET ADFuncties.)
-- =====================================================================

SELECT DISTINCT
    sis_leer.stamnr       AS Leerlingnummer,
    sis_leer.roepnaam     AS Voornaam,
    sis_leer.tussenvoeg   AS Tussenvoegsel,
    sis_leer.achternaam   AS Achternaam,
    sis_leer.email        AS Email,
    sis_blok.omschr       AS Locatie,
    sis_bgrp.groep        AS Klas          -- alleen ter controle, NIET importeren in de app
FROM sis_leer sis_leer
    INNER JOIN sis_aanm sis_aanm ON sis_leer.stamnr    = sis_aanm.stamnr
    LEFT  JOIN sis_bgrp sis_bgrp ON sis_aanm.idBgrp    = sis_bgrp.idBgrp
    LEFT  JOIN sis_blok sis_blok ON sis_bgrp.c_lokatie = sis_blok.c_lokatie
WHERE
    -- Peildatum in het KOMENDE schooljaar (later parametriseren met #peildatum#):
    sis_aanm.dBegin    <= '2026-08-01'
    AND sis_aanm.dEinde    >= '2026-08-01'
    AND (sis_aanm.dVertrek >= '2026-08-01' OR sis_aanm.dVertrek IS NULL)
ORDER BY sis_leer.stamnr;

-- Optioneel - beperk tot bepaalde vestiging(en):
--   AND sis_blok.c_lokatie IN ('...')
--
-- Alternatief next-year-filter via STUDYPERIOD (als de peildatum niet bevalt):
--   LEFT JOIN sis_allp ON sis_aanm.stamnr = sis_allp.stamnr AND sis_aanm.lesperiode = sis_allp.lesperiode
--   LEFT JOIN sis_blpe ON sis_allp.lesperiode = sis_blpe.lesperiode
--   WHERE sis_blpe.omschr_k = '2026-2027'
