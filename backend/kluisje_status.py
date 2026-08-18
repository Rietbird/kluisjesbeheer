"""Wanneer is een kluisje echt uitleenbaar.

`kluisjes.status` kent alleen 'vrij', 'uitgeleend' en 'defect', maar defect en
"geen sleutel" zijn daarnaast losse vlaggen die blijven staan terwijl de status
gewoon 'vrij' is. Een defect kluisje zonder huurder heeft dus status 'vrij'.

Filteren op status alleen laat die er daarom tussen staan. Dat ging drie keer
mis tegelijk: in het statusfilter op het kluisjesscherm, in de teller 'Vrij' op
het dashboard, en in de wizard voor collectief toekennen, die defecte kluisjes
meetelde als beschikbaar en ze vervolgens door de server liet weigeren.

De toewijsroutes hanteerden deze regel al wel (409 bij defect of geen sleutel);
het waren de filters en tellers die achterliepen.
"""

UITLEENBAAR_SQL = "k.status = 'vrij' AND k.is_defect = 0 AND k.geen_sleutel = 0"
