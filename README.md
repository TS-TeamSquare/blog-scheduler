# blog-scheduler — publication programmée des 82 blogs satellites Team Square

Remplace la tâche Claude « toutes les 3h ». Les articles sont **pré-poussés avec une date future** ;
le template Nuxt les masque tant que `date > maintenant` (validé en live le 27/06). Un **cron horaire**
redéploie chaque site **au moment exact de son créneau** pour rafraîchir l'index et le sitemap.

## Anti-collision (exigence Julien)
Chaque site a un **créneau jour + heure UNIQUE** — aucun des 82 sites ne publie au même moment :
- jour = `i % 7` (réparti sur 7 jours, ~12 sites/jour) ;
- heure = `8 + (i // 7)` (08h→19h, une heure différente par site le même jour) ;
- minute déterministe pour un rendu organique.
Cadence : 1 article/site tous les 7 jours, toujours sur le même créneau.
Contrôle automatique : `planifier.py` affiche « collisions: 0 ».

## Contenu du repo
- `calendrier-publication.csv` — date | repo | domaine | ville | activite | titre | article | statut (planned→pushed→deployed)
- `planifier.py` — assigne les créneaux + dates futures, écrit le calendrier ; `--push [N]` pousse les articles datés-futur.
- `redeploy_due.py` — red