# Spec: Clusters verwijderen (concierge) via soft-delete

- **Datum:** 2026-06-24
- **Status:** ontwerp (goedgekeurd door Vincent)

## Probleem

Concierges kunnen kluisjes binnen een cluster beheren, maar een cluster zelf
"verwijderen" lukt niet. De echte blokkade was niet de rechten (de DELETE-route
had al geen beheerder-check) maar de logica:

- `delete_cluster` gaf **409** zodra er *ook maar één* (ook historische)
  toewijzing in het cluster zat — en deed daarna een **harde** delete van de
  kluisjes. In de praktijk heeft bijna elk cluster historie → de knop faalde altijd.

## Doel

Een cluster kunnen verwijderen zonder historie te verliezen.

## Ontwerp

- Nieuwe kolom `clusters.verwijderd INTEGER NOT NULL DEFAULT 0` (migratie in `db.py`).
- `delete_cluster`:
  - Blokkeer (409) alleen nog op **actieve** toewijzingen (`t.actief = 1`).
  - Anders **soft-delete**: zet `verwijderd = 1` op het cluster én op zijn kluisjes.
    De toewijzing-historie blijft intact (verwijst naar de soft-deleted kluisjes),
    net zoals bij het soft-deleten van losse kluisjes.
- `list_clusters` filtert op `verwijderd = 0`.
- Rechten blijven ongewijzigd: `@login_required` + `assert_vestiging_access`
  (concierge mag binnen eigen vestiging; beheerder overal) — dat was Vincents wens.

## Niet-doel
- Geen frontend-wijziging: de verwijder-knop in ClustersPanel bestaat al en roept
  hetzelfde endpoint aan. Alleen het gedrag verandert (slaagt nu bij historie).
- Geen "prullenbak"/herstel-UI voor verwijderde clusters (kan later).

## Tests (`test_cluster_delete.py`)
- Cluster met historische toewijzing → 200, cluster weg uit lijst, geschiedenis behouden.
- Cluster met actieve toewijzing → 409.
- Kluisjes van een verwijderd cluster verdwijnen uit het overzicht.

## Deploy
Migratie draait bij startup. Eerst CT102, dan CT101.
