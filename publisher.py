#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import csv, os, re, sys, subprocess, tempfile, shutil, datetime, random
BASE = os.path.dirname(os.path.abspath(__file__))
TOKEN_FILE = os.path.join(BASE, "jeton-github.txt")
RESERVOIR  = os.path.join(BASE, "..", "reservoir-articles.csv")
LOG        = os.path.join(BASE, "journal-publication.txt")
N = int(sys.argv[1]) if len(sys.argv) > 1 else 6
ORG = "TS-TeamSquare"; TS = "https://team-square.fr/"
SIGN = "par ceux qui animent vos sorties"   # signature des articles auto
FICHE = {
 "Paintball":"activiteTeamSquare/paintball","Karaoké":"activiteTeamSquare/karaoke",
 "Bubble Foot":"activiteTeamSquare/bubble-foot","Lancer de hache":"activiteTeamSquare/lancer-de-hache",
 "Réalité virtuelle":"activiteTeamSquare/realite-virtuelle","Quiz":"activiteTeamSquare/quizz",
 "Escape Game":"activiteTeamSquare/chasse-au-tresor","Simulateur de vol":"activiteTeamSquare/simulateur-f1-gt",
 "Action Game":"activiteTeamSquare/laser-game","Activités":"activiteTeamSquare/paintball",
 "Séminaire":"seminaire-rentree-entreprise-nord","Team Building":"seminaire-rentree-entreprise-nord",
 "Anniversaire":"anniversaire-ado-idees-activites-nord","Mariage":"bapteme-communion-salle-reception-nord",
 "Baptême":"bapteme-communion-salle-reception-nord","Communion":"bapteme-communion-salle-reception-nord",
 "EVG":"evg-arras-activites-enterrement-vie-garcon","EVJF":"evjf-arras-lens-activites-originales",
 "Enterrement de vie de célibataire":"evg-arras-activites-enterrement-vie-garcon",
 "Espace de réception":"bapteme-communion-salle-reception-nord","Location de salles":"bapteme-communion-salle-reception-nord"}
OCC = [("anniversaire-ado-idees-activites-nord","idées d'anniversaire"),("evg-arras-activites-enterrement-vie-garcon","organiser un EVG"),
       ("evjf-arras-lens-activites-originales","un EVJF original"),("sortie-cse-nord-activites-comite-entreprise","une sortie CSE")]


PREFIX = {"Paintball":"pb","Karaoké":"kar","Bubble Foot":"bf","Lancer de hache":"lh","Réalité virtuelle":"rv",
 "Quiz":"qz","Escape Game":"eg","Simulateur de vol":"sim","Action Game":"ag","Activités":"ac","Séminaire":"sem",
 "Team Building":"tb","Anniversaire":"anniv","Mariage":"mariage","Baptême":"bapteme","Communion":"communion",
 "EVG":"evg","EVJF":"evjf","Enterrement de vie de célibataire":"celib","Espace de réception":"reception","Location de salles":"salles"}

try:
    from angles_extra import ANG_EXTRA, TOPICS_EXTRA
except Exception:
    ANG_EXTRA, TOPICS_EXTRA = {}, {}

import glob as _glob
def used_images(content_dir, exclude=None):
    used=set()
    for f in _glob.glob(os.path.join(content_dir,"**","*.md"), recursive=True):
        if exclude and os.path.abspath(f)==os.path.abspath(exclude): continue
        try: txt=open(f,encoding="utf-8").read()
        except Exception: continue
        for m in re.findall(r"/img/([^)\"\\s]+\.(?:jpg|jpeg))", txt, re.I):
            used.add(m.split("/")[-1])
    return used

def pick_images(img_dir, pref, used=frozenset()):
    try:
        files=[f for f in os.listdir(img_dir) if f.lower().endswith((".jpg",".jpeg")) and not any(x in f.lower() for x in ("logo","icon","favicon","og-","cookie","sans-titre"))]
    except Exception:
        files=[]
    if not files:
        return f"/img/{pref}-hero.jpg", f"/img/{pref}-2.jpg"
    avail=[f for f in files if f not in used]
    if len(avail)>=2:
        c=random.sample(avail,2)
    elif len(avail)==1:
        other=[f for f in files if f!=avail[0]] or files
        c=[avail[0], random.choice(other)]
    else:
        c=random.sample(files,2) if len(files)>=2 else [files[0],files[0]]
    return f"/img/{c[0]}", f"/img/{c[1]}"

def _el(s, a):
    if a and a[0].lower() in "aàâeéèêiîoôuûy":
        for x,y in [("le "+a,"l'"+a),("Le "+a,"L'"+a),("de "+a,"d'"+a),("De "+a,"D'"+a),("du "+a,"de l'"+a),("que le "+a,"que l'"+a),("séance de "+a,"séance d'"+a)]:
            s=s.replace(x,y)
    return s

def article_md(title, loc, act, cover, img2):
    a = act.lower(); fiche = FICHE.get(act, "activite"); tl = title.lower()
    CAT = {"Séminaire":"b2b","Team Building":"b2b",
           "EVG":"party","EVJF":"party","Enterrement de vie de célibataire":"party","Anniversaire":"party",
           "Mariage":"venue","Baptême":"venue","Communion":"venue","Espace de réception":"venue","Location de salles":"venue"}
    cat = CAT.get(act, "loisir")
    UN = {"EVG":"un EVG","EVJF":"un EVJF","Enterrement de vie de célibataire":"un enterrement de vie de célibataire",
          "Anniversaire":"un anniversaire","Mariage":"un mariage","Baptême":"un baptême","Communion":"une communion",
          "Espace de réception":"une réception","Location de salles":"une location de salle",
          "Séminaire":"un séminaire","Team Building":"un team building"}
    un = UN.get(act, "un "+a)
    anchors = ["Team Square", "team-square.fr", "le site officiel de Team Square", "réserver en ligne", "en savoir plus", "voir les détails", "découvrir "+un, "Team Square à Hénin-Beaumont"]
    random.shuffle(anchors); a1, a2 = anchors[0], anchors[1]
    def fmt(s): return s.replace("{a}",a).replace("{act}",act).replace("{loc}",loc).replace("{un}",un)
    access = ("## Accès et infos pratiques\n\nTeam Square se trouve à **Hénin-Beaumont (3 Chemin de Bois Bernard, 62110)**, "
        "à **25 minutes de Lille par l'A1**, à 10 minutes de Lens et de Douai et à 20 minutes d'Arras — un point de rendez-vous central pour réunir vos invités venus de toute la région. "
        "Le **parking est gratuit et surveillé**, et le complexe est ouvert toute la semaine. Pour en savoir plus, rendez-vous sur ["+a2+"]("+TS+fiche+"/).\n\n")
    stats="::ts-stats\n::\n\n"; img=fmt("![{act} {loc} chez Team Square]("+img2+")\n\n")
    promo_ts10=("::ts-promo{button=\"Réserver en ligne\"}\n#title\n🎟️ −10% avec le code TS10\n#default\n"
        "Réservez vos activités en ligne avec le code **TS10** — paiement à la réservation, offre valable même le samedi.\n::\n\n")
    promo_devis=("::ts-promo{button=\"Demander un devis\"}\n#title\n📝 Un devis clair, sans engagement\n#default\n"
        "Dites-nous votre projet (date, nombre d'invités, envies) : on vous prépare un devis détaillé, poste par poste, valable 30 jours.\n::\n\n")
    fm=("---\ntitle: \""+title+"\"\ntagline: \""+act+" "+loc+" chez Team Square, "+SIGN+".\"\n"
        "description: \""+title+" — conseils, formules, déroulé, accès et FAQ chez Team Square, à 25 minutes de Lille.\"\n"
        "date: "+(datetime.date.today()-datetime.timedelta(days=random.randint(2,150))).isoformat()+"T09:00:00.000Z\ncategory: \""+act+"\"\ncoverImage: "+cover+"\n"
        "summarySeo: \""+title+" : tout savoir pour organiser "+un+" "+loc+" chez Team Square.\"\n---\n\n")
    # ----- angles (intro + 1re section) : ~10 par catégorie ; le reste est mutualisé -----
    ANG = {
    "loisir":[
      (("coûte","tarif","budget","prix","cher"),"Vous prévoyez une sortie {a} {loc} et vous vous demandez quel budget prévoir ? On fait le point sur le prix par personne, les formules de groupe et les bons plans pour payer moins cher.","Combien coûte une session ?","Le {a} se réserve à des tarifs pensés pour les groupes, avec une grille en semaine et une le samedi. Le prix s'entend par personne et dépend de la durée. En réservant en ligne, le **code TS10** vous fait économiser **10 %** sur le tarif du jour."),
      (("que faire","week-end","weekend"),"En manque d'idées pour ce week-end {loc} ? Le {a} fait partie de ces sorties qui mettent tout le monde d'accord : on se retrouve, on se dépense, on repart avec des souvenirs.","Pourquoi le {a} est une valeur sûre","Tout est réuni au même endroit : le {a}, un animateur dédié, un bar et plus de 22 activités. Vous arrivez, vous jouez, vous prolongez avec une autre activité, sur un site de 7 500 m² à 25 minutes de Lille."),
      (("quel âge","quel age","joueurs","combien faut"),"Avant de réserver votre {a} {loc}, deux questions reviennent souvent : à partir de quel âge, et combien faut-il être ? On vous répond clairement pour constituer votre groupe sereinement.","Âge minimum et taille du groupe","Le {a} est encadré par un animateur dédié et accessible dès un petit groupe. Chaque session s'adapte à l'âge et au nombre de participants. Un doute sur la composition du groupe ? Un appel suffit pour être conseillé."),
      (("anniversaire",),"Pour marquer le coup, organiser un anniversaire autour du {a} {loc} est une valeur sûre : du fun pour tous les âges, un cadre sécurisé et zéro organisation pour vous.","Une fête d'anniversaire clé en main","On s'occupe de tout : l'activité encadrée, un espace privatisable, et même le gâteau et les surprises pour les plus jeunes. Vous composez la fête selon l'âge du groupe, et vous n'avez plus qu'à profiter."),
      (("evg","evjf","enterrement de vie"),"Pour l'EVG ou l'EVJF du futur marié, le {a} {loc} est un incontournable : adrénaline, fous rires et souvenirs garantis entre amis.","L'activité parfaite pour un enterrement de vie","Le {a} a tout pour plaire à un groupe d'amis : de l'action et de quoi mettre le ou la futur(e) marié(e) à l'honneur. On compose la journée selon vos envies, avec la possibilité de prolonger par un pack soirée privatisé."),
      (("pluie","mauvais temps","météo","meteo"),"La météo {loc} menace votre sortie ? Pas de panique : le {a} en salle chez Team Square, c'est l'assurance d'une journée réussie quel que soit le temps.","Une sortie à l'abri, quoi qu'il arrive","Nos espaces indoor couvrent 7 500 m² et vous accueillent toute l'année. Le {a} se pratique à couvert, et vous pouvez enchaîner avec d'autres activités sans remettre le nez dehors."),
      (("collègues","team building","entreprise","cohésion","cohesion"),"Envie de souder vos équipes {loc} ? Le {a} est un excellent prétexte pour sortir du bureau et resserrer les liens dans une ambiance détendue.","Le {a} pour souder une équipe","Rien de tel qu'un défi commun pour créer du lien : le {a} mêle esprit d'équipe, communication et bonne humeur. On adapte la formule à la taille de votre groupe, et on peut compléter par une salle de réunion ou un repas."),
      (("cadeau","offrir"),"À court d'idée cadeau {loc} ? Offrir une séance de {a} change des présents classiques : une expérience à vivre, des souvenirs plutôt qu'un objet.","Offrir une expérience plutôt qu'un objet","Une séance de {a} se prête à tous les prétextes : anniversaire, fête, remerciement. On vous oriente sur la formule et la durée selon le profil de la personne, et il ne reste qu'à réserver le créneau."),
      (("première fois","premiere fois","débutant","debutant","jamais"),"C'est votre première fois au {a} {loc} ? Pas besoin d'être un pro : on vous explique tout pour aborder votre session sereinement et en profiter à fond.","Débuter le {a} sans stress","Aucune expérience requise : un animateur dédié explique les règles et la sécurité avant de lancer la session, et adapte le rythme aux débutants. Une tenue confortable et l'envie de s'amuser suffisent."),
      (("famille","enfants","enfant","petits"),"Envie d'une sortie en famille {loc} qui plaise autant aux enfants qu'aux parents ? Le {a} réunit petits et grands autour d'un bon moment partagé.","Une activité pour toute la famille","On adapte le {a} à l'âge des participants pour que chacun trouve sa place, du plus jeune au plus grand. Encadrement par un animateur dédié, sécurité, et la possibilité d'enchaîner avec d'autres activités du parc pour une vraie journée en famille."),
      (("combien de temps","durée","duree","temps prévoir"),"Combien de temps prévoir pour une séance de {a} {loc} ? On vous aide à caler la durée idéale selon votre groupe et vos envies.","Quelle durée choisir ?","Le {a} se réserve sur des créneaux de différentes durées : court pour une découverte, plus long pour profiter à fond ou pour un grand groupe en rotation. Comptez aussi 15 minutes d'accueil avant, et la possibilité d'enchaîner une seconde activité ensuite."),
      (("grand groupe","grand nombre","beaucoup de monde","gros groupe"),"Vous êtes nombreux et cherchez une activité {loc} qui tienne la route pour un grand groupe ? Le {a} se prête parfaitement aux effectifs importants.","Le {a} pour les grands groupes","Sur 7 500 m² avec plusieurs espaces et une rotation possible sur les activités, on accueille de grands groupes sans souci. On dimensionne l'encadrement et le planning à votre nombre, et une tournée de boissons peut être offerte entre deux activités."),
      (("indoor","outdoor","intérieur","exterieur","extérieur"),"Indoor ou outdoor pour votre {a} {loc} ? On vous explique les options pour profiter quelle que soit la saison.","Indoor, outdoor : on s'adapte","Team Square combine 7 500 m² indoor et de vastes espaces outdoor. Selon l'activité, la météo et la saison, on vous oriente vers la meilleure configuration — et l'indoor garantit une sortie réussie même quand le ciel n'est pas de la partie."),
      (("sécurité","securite","encadrement","encadré"),"La sécurité est votre priorité pour une sortie {a} {loc} ? On vous explique comment chaque session est encadrée.","Un encadrement sérieux à chaque session","Chaque activité est encadrée par un animateur dédié, avec un briefing de sécurité avant de commencer et du matériel adapté. Les équipes sont formées en continu, et l'organisation est pensée pour que chacun s'amuse en toute sécurité, débutant comme habitué."),
      (("après l'activité","apres l'activite","prolonger","après votre"),"Que faire après votre {a} {loc} ? Bonne nouvelle : la journée ne s'arrête pas forcément à la fin de l'activité.","Prolonger la journée au parc","Après le {a}, on peut souffler au bar, enchaîner avec l'une des 22 autres activités, ou privatiser un espace pour un repas ou une soirée. Tout est au même endroit sur 7 500 m², de quoi transformer une activité en vraie journée."),
      (("venir de","depuis","accès","acces","trajet"),"Vous venez des environs et voulez tester le {a} {loc} ? Team Square est facile d'accès depuis toute la région.","Un accès simple depuis toute la région","Le parc est à Hénin-Beaumont, à 25 minutes de Lille par l'A1, 10 minutes de Lens et de Douai, 20 minutes d'Arras, avec un parking gratuit et surveillé. Un point de rendez-vous central pour réunir un groupe venu de plusieurs villes."),
      (("cse","comité d'entreprise","comité","comite"),"Vous organisez une sortie pour votre CE ou CSE {loc} ? Le {a} est une valeur sûre pour réunir les collaborateurs et leurs familles.","Une sortie CSE qui plaît à tous","Le {a} s'intègre dans une sortie comité d'entreprise simple à organiser : activités encadrées, espace privatisable, restauration sur place. On bâtit une formule adaptée à votre effectif, avec un seul interlocuteur pour tout caler."),
      (("scolaire","centre de loisirs","école","ecole","colonie"),"Vous encadrez un groupe scolaire ou un centre de loisirs et cherchez une activité {a} {loc} sûre et adaptée ? On vous accompagne.","Groupes scolaires et centres de loisirs","Le {a} se prête bien aux groupes encadrés : sécurité, animateur dédié, formules de groupe et activités adaptées à l'âge. On organise la journée avec vous, du planning à la restauration, pour une sortie fluide et mémorable."),
      (("été","ete","hiver","saison","vacances"),"Quelle activité {a} {loc} selon la saison ? Été comme hiver, le {a} reste une sortie au top.","Une sortie pour toutes les saisons","Grâce aux 7 500 m² indoor, le {a} se pratique toute l'année, à l'abri du froid l'hiver comme de la pluie. L'été, les espaces outdoor offrent encore plus de possibilités. C'est l'idée de sortie qui ne dépend pas de la météo."),
      (("tenue","prévoir","equipement","équipement","apporter"),"Que prévoir et quelle tenue pour votre {a} {loc} ? Quelques conseils pratiques pour arriver paré.","Ce qu'il faut prévoir","Prévoyez une tenue confortable adaptée à l'activité et des chaussures fermées ; le matériel nécessaire est fourni sur place. Arrivez une quinzaine de minutes avant le créneau pour l'accueil, et pensez au **code TS10** pour −10 % en réservant en ligne."),
      (("niveau","confirmé","confirme","expérimenté","experimente"),"Débutant ou confirmé, le {a} {loc} s'adapte à votre niveau. On vous explique comment.","Du débutant au confirmé","Le {a} se savoure à tous les niveaux : l'animateur adapte le rythme et les règles selon le groupe, pour que les débutants progressent et que les habitués se challengent. Idéal pour mélanger les profils sans que personne ne s'ennuie."),
      (("",),"Réussir une sortie de groupe {loc}, ça se prépare un minimum. Voici nos meilleures astuces pour que votre {a} se passe sans accroc, du premier au dernier participant.","Bien préparer sa sortie en groupe","Le {a} prend tout son sens à plusieurs. Réservez à l'avance, surtout le samedi, prévenez de la taille exacte du groupe pour un encadrement optimal, et combinez le {a} avec une deuxième activité pour rythmer la journée."),
    ],
    "party":[
      (("coûte","tarif","budget","prix"),"Vous organisez {un} {loc} et vous voulez cadrer le budget ? Entre les activités, la privatisation et la restauration, on vous explique comment composer une journée mémorable sans exploser la note.","Quel budget prévoir ?","Les activités se réservent par personne, avec une grille en semaine et une le samedi, et le **code TS10** offre −10 % en ligne. Pour les grands groupes, on bâtit une formule sur mesure et on peut ajouter un pack soirée. On chiffre tout clairement à l'avance."),
      (("idées","idee","activités","activites"),"Vous organisez {un} {loc} et vous cherchez les meilleures idées d'activités ? Tour d'horizon des incontournables pour une journée qui décoiffe.","Nos activités qui rassemblent","Paintball, laser game, bubble foot, réalité virtuelle, simulateurs, lancer de hache, karaoké… plus de 22 activités à combiner selon les envies du groupe, sur 7 500 m² à 25 minutes de Lille, encadrées par un animateur dédié."),
      (("programme","journée","journee","déroulé","deroule"),"À quoi ressemble {un} réussi {loc} ? On vous déroule le programme type d'une journée Team Square, des premières activités à la soirée.","Le programme d'une journée réussie","On alterne temps forts et pauses : une ou deux activités à sensations, une tournée offerte entre deux activités enchaînées, puis une soirée privatisée si vous le souhaitez. De quoi transformer une après-midi en moment inoubliable."),
      (("soirée","soiree","privatisé","privatise","nuit"),"Et si {un} {loc} se prolongeait par une soirée rien qu'à vous ? Salle privatisée, restauration et karaoké : on vous dit tout.","Une soirée privatisée pour finir en beauté","Le pack soirée privatisé réunit une salle rien que pour vous, une restauration au choix (cocktail dînatoire, burgers, pizzas), des boissons et le karaoké. La fête peut se prolonger tard, pour une ambiance qui ne retombe pas."),
      (("participants","invités","invites"),"Combien peut-on être pour {un} {loc} ? On vous explique comment on adapte les activités et la privatisation à la taille de votre groupe.","Petit ou grand groupe, on s'adapte","De quelques amis à de grands groupes, on dimensionne les activités et la salle au nombre de participants. Plusieurs formules permettent d'accueillir au-delà de la dizaine, en rotation sur les activités. Un appel suffit pour caler tout ça."),
      (("pluie","météo","meteo"),"La météo {loc} menace {un} ? Aucun souci : la plupart des activités se déroulent à l'abri, sur 7 500 m² en indoor.","À l'abri quelle que soit la météo","Nos espaces couverts accueillent votre groupe toute l'année. On enchaîne les activités sans dépendre du ciel, et la soirée privatisée se déroule évidemment au chaud. La pluie ne gâchera pas la fête."),
      (("organiser","guide","préparer","preparer"),"Vous vous lancez dans l'organisation {un} {loc} ? Voici le guide complet pour ne rien oublier et profiter à fond le jour J.","Organiser sans prise de tête","On vous accompagne du choix des activités à la privatisation : il suffit d'indiquer la date, le nombre de participants et vos envies. L'équipe propose la formule, et vous gardez la main sur le programme."),
      (("surprendre","original","originale","surprise"),"Envie de surprendre le groupe pour {un} {loc} ? Quelques idées pour sortir des sentiers battus et marquer les esprits.","Des idées pour surprendre","Misez sur des activités à sensations méconnues, les options déguisements et tee-shirts personnalisés pour le héros du jour, et une soirée privatisée surprise. On combine plusieurs activités pour un effet 'waouh' garanti."),
      (("pas cher","bons plans","économiser","economiser"),"Organiser {un} {loc} sans se ruiner, c'est possible : voici nos bons plans pour maîtriser le budget tout en se faisant plaisir.","Nos bons plans pour le budget","Réservez en semaine quand c'est possible (tarif plus doux), profitez du **code TS10** pour −10 % en ligne, et regroupez les participants pour optimiser les formules. La tournée offerte entre deux activités fait aussi plaisir au porte-monnaie."),
      (("déguisement","deguisement","tee-shirt","héros","heros"),"Comment mettre le héros du jour à l'honneur pour {un} {loc} ? Petits plus et options qui font la différence.","Mettre le héros du jour à l'honneur","Déguisements et tee-shirts personnalisés permettent de distinguer le futur marié, la future mariée ou le fêté du jour. Combinés à des gages entre deux activités et à une soirée privatisée, ils transforment la journée en souvenir mémorable."),
      (("famille","enfants","tous les âges","tous les ages"),"Vous organisez {un} {loc} qui mêle plusieurs générations ? On adapte pour que petits et grands s'amusent ensemble.","Une fête pour tous les âges","On compose un programme accessible à tous : activités douces pour les plus jeunes, plus de sensations pour les ados et adultes, le tout encadré. Un espace privatisable et la restauration sur place complètent une fête qui rassemble toute la tribu."),
      (("combien de temps","durée","duree","temps prévoir"),"Combien de temps prévoir pour {un} {loc} ? On vous aide à caler le timing idéal.","Quelle durée pour la journée ?","Comptez une à plusieurs heures d'activités selon le nombre d'envies, plus une éventuelle soirée privatisée pour prolonger. On cale le planning avec vous (arrivée, activités, pauses, repas) pour une journée fluide sans temps mort."),
      (("réserver","reserver","quand","s'y prendre"),"Quand et comment réserver {un} {loc} ? Mieux vaut s'y prendre à l'avance, on vous explique.","Réserver au bon moment","Les samedis et les périodes de fêtes partent vite : réservez tôt. À moins de 72 h, la réservation se fait par téléphone pour bien dimensionner l'encadrement. Le règlement en ligne avec le **code TS10** vous fait économiser 10 %."),
      (("restauration","repas","manger","traiteur"),"Quelle restauration pour {un} {loc} ? De la formule rapide au cocktail dînatoire, on s'adapte à votre groupe.","Bien manger après l'effort","Selon la formule, on propose burgers-frites, pizzas, suprêmes ou un cocktail dînatoire de plusieurs bouchées par personne, avec tickets boissons. Une tournée est offerte entre deux activités, et la restauration se prend dans un espace privatisable."),
      (("",),"Vous organisez {un} {loc} et vous voulez un moment inoubliable ? Voici nos conseils pour réussir votre événement de A à Z.","Nos conseils pour réussir","Réservez tôt (les samedis partent vite), prévenez du nombre exact de participants, combinez deux activités pour varier les plaisirs, et pensez à la soirée privatisée pour prolonger. À moins de 72 h, la réservation se fait par téléphone."),
    ],
    "venue":[
      (("coûte","tarif","budget","prix"),"Vous organisez {un} {loc} et vous voulez cadrer votre budget ? Entre la location de la salle, le traiteur, les boissons et les options, on fait le point pour un devis clair, sans mauvaise surprise.","Combien ça coûte ?","Le prix dépend de la salle, du nombre d'invités et des prestations. Un **acompte de 30 %** valide la réservation, le solde se règle avant l'événement, et le **devis reste valable 30 jours**. On construit un devis détaillé, poste par poste."),
      (("capacité","capacite","invités","invites","combien de personnes","nombre"),"Combien d'invités pouvez-vous accueillir pour {un} {loc} ? On vous présente nos salles et leurs capacités pour choisir le bon espace.","Des salles de 20 à 200 personnes","Team Square Events propose plusieurs salles privatisées, de 20 à 200 personnes. On vous oriente vers l'espace le mieux adapté à votre nombre d'invités et à l'ambiance souhaitée, équipé de tables, chaises, vidéoprojecteur et sonorisation."),
      (("traiteur","menu","repas","restauration"),"Quelle restauration pour {un} {loc} ? Tour d'horizon de notre carte traiteur maison, du cocktail dînatoire au menu complet.","Un traiteur maison à la carte","Notre cuisine propose apéritifs et cocktails dînatoires, buffets froids, plats traditionnels et **menu oriental 100 % Halal** sur demande. Les boissons sont en libre-service, et la vaisselle est incluse dès que traiteur et boissons sont pris chez nous."),
      (("décoration","decoration","aménagement","amenagement"),"Comment décorer et aménager votre salle pour {un} {loc} ? Nos possibilités et nos règles pour un cadre à votre image.","Décoration et aménagement","La salle privatisée vous laisse libre de la décorer (installation possible la veille selon disponibilité). Tables rondes ou rectangulaires, mange-debout, agencement : on cale tout au rendez-vous des 15 jours. Quelques règles simples préservent les lieux."),
      (("déroulé","deroule","journée type","journee type","programme"),"À quoi ressemble {un} {loc} chez Team Square ? On vous déroule une réception type, de l'accueil à la fin de soirée.","Le déroulé d'une réception type","Accueil des invités, apéritif, repas servi par nos équipes, temps forts et soirée : tout est rythmé avec vous. Avec l'astreinte, l'événement peut se prolonger **jusqu'à 5 h du matin**, n'importe quel jour de la semaine."),
      (("réserver","reserver","mode d'emploi","démarches","demarches"),"Comment réserver une salle pour {un} {loc} ? On vous explique les étapes, du premier contact à la confirmation.","Réserver en quelques étapes","On part de votre projet (date, invités, envies) pour bâtir un devis. Un **acompte de 30 %** confirme la réservation, le devis est valable 30 jours, et une coordinatrice prend ensuite le relais jusqu'au jour J."),
      (("tout inclus","clé en main","cle en main","formule"),"Location seule ou formule tout inclus pour {un} {loc} ? On compare les deux options pour vous aider à choisir.","Location seule ou clé en main","Deux possibilités : la **location de salle seule**, ou la formule **clé en main** avec traiteur et boissons servis par nos équipes. La formule clé en main simplifie tout et inclut la vaisselle. On vous chiffre les deux pour comparer."),
      (("heure","tard","minuit","jusqu'à quelle"),"Jusqu'à quelle heure peut durer {un} {loc} ? Bonne nouvelle pour les fêtes qui se prolongent.","Une fête qui peut durer jusqu'à 5 h","Grâce à un membre d'astreinte, votre événement peut se poursuivre **jusqu'à 5 h du matin**, et ce n'importe quel jour de la semaine. De quoi profiter pleinement de la soirée sans regarder l'horloge."),
      (("organiser","guide","préparer","preparer"),"Vous vous lancez dans l'organisation {un} {loc} ? Voici le guide complet pour avancer sereinement, étape par étape.","Organiser sans stress","De la salle au traiteur, on vous accompagne de bout en bout. Après le devis et l'acompte, une coordinatrice événementielle pilote les détails, et le rendez-vous des 15 jours fige menus, planning et agencement. Vous profitez, on s'occupe du reste."),
      (("boissons","champagne","vin","alcool"),"Quelles boissons pour {un} {loc} ? Du soft au champagne, on vous présente les options.","Boissons : softs, vins et champagnes","La carte propose softs, bières, vins et champagnes, en libre-service ou au ticket selon la formule. La vaisselle et la verrerie sont incluses dès que les boissons et le traiteur sont pris chez nous. On adapte les quantités à votre nombre d'invités."),
      (("enfants","animation","famille"),"Comment occuper les enfants pendant {un} {loc} ? Quelques idées pour que les plus jeunes passent aussi un bon moment.","Penser aussi aux enfants","Au-delà de la réception, le parc compte plus de 22 activités et des espaces adaptés aux familles. On peut prévoir un coin ou une animation pour les enfants, voire une activité encadrée, pour que les parents profitent sereinement de la fête."),
      (("acompte","caution","conditions","paiement"),"Acompte, caution, délais : quelles conditions pour réserver {un} {loc} ? On clarifie tout.","Acompte, devis et conditions","Un **acompte de 30 %** valide la réservation après acceptation du devis (valable 30 jours) ; le solde se règle avant l'événement, et un chèque de caution est demandé puis restitué s'il n'y a pas de dégât. Tout est cadré clairement dès le devis."),
      (("saison","période","periode","quand se marier","date"),"Quelle période choisir pour {un} {loc} ? On vous aide à anticiper selon la saison et la disponibilité.","Bien choisir sa date","Les samedis et la fin d'année partent très vite : plus vous anticipez, plus vous avez de choix de salle et de créneau. On vous conseille sur les périodes les plus demandées et on bloque votre date dès l'acompte versé."),
      (("",),"Vous préparez {un} {loc} ? Voici nos conseils pour une organisation réussie, du premier devis au jour J.","Nos conseils d'organisation","Réservez tôt — les samedis et la fin d'année partent vite. Soignez le nombre d'invités au plus juste, le choix du menu selon vos convives, et la décoration. Notre équipe vous conseille à chaque étape pour un événement à votre image."),
    ],
    "b2b":[
      (("coûte","tarif","budget","prix"),"Vous organisez {un} {loc} et vous voulez cadrer le budget ? Entre la salle de réunion, les activités de cohésion et la restauration, on vous explique comment bâtir une journée efficace au bon prix.","Quel budget pour votre journée ?","Le tarif se construit sur devis selon vos effectifs et vos besoins. Une **formule séminaire tout inclus** (petit-déjeuner, salle, déjeuner, activités) simplifie la facturation. On vous chiffre tout clairement, sans engagement."),
      (("cohésion","cohesion","activités de cohésion","activites de cohesion"),"Quelles activités de cohésion pour {un} {loc} ? Sélection des incontournables pour souder vos équipes.","Des activités qui rassemblent","Olympiades, escape game, paintball, laser game, bubble foot, simulateurs… on sélectionne avec vous les activités les plus adaptées à vos objectifs : cohésion, communication, gestion du stress. Chaque activité est encadrée par un animateur dédié."),
      (("salle","réunion","reunion"),"Quelles salles pour {un} {loc} ? Tour d'horizon de nos espaces de réunion équipés.","Des salles de réunion équipées","Nos salles s'adaptent de la petite équipe au grand groupe, en demi-journée ou journée, avec vidéoprojecteur et sonorisation. Elles se combinent avec les activités du parc pour alterner travail et cohésion, sans déplacement."),
      (("participants","combien","effectif","nombre"),"Combien de participants pour {un} {loc} ? On vous explique comment on dimensionne salles et activités.","De la petite équipe au grand groupe","Des petites équipes à plusieurs centaines de personnes, on dimensionne salles et activités selon vos effectifs. Plusieurs espaces permettent d'accueillir de grands groupes en rotation. Tout se cale sur devis."),
      (("tout inclus","formule","clé en main","cle en main"),"Une formule clé en main pour {un} {loc} ? On vous présente le séminaire tout inclus.","La formule séminaire tout inclus","Petit-déjeuner, salle de réunion, déjeuner et activités de mise en pratique réunis dans une formule unique : l'organisation et la facturation sont simplifiées. Idéale pour une journée d'entreprise sans logistique à gérer."),
      (("restauration","traiteur","repas","déjeuner","dejeuner"),"Quelle restauration pour {un} {loc} ? Pauses, déjeuner et cocktail : notre cuisine s'adapte.","Restauration sur place","Pause petit-déjeuner, déjeuner sur place, cocktail de clôture : notre cuisine compose des formules adaptées à votre journée, **menu oriental Halal sur demande**. Tout est sur place, pour ne pas couper le rythme de la journée."),
      (("objectifs","communication","stress","conflit"),"Quels objectifs viser avec {un} {loc} ? Cohésion, communication, gestion du stress : on adapte les activités à vos enjeux.","Des activités au service de vos objectifs","On choisit les activités selon ce que vous visez : renforcer la cohésion, fluidifier la communication, apprendre à gérer le stress ou simplement décompresser ensemble. Chaque format est pensé pour faire travailler le collectif."),
      (("journée type","journee type","déroulé","deroule","programme"),"À quoi ressemble {un} {loc} chez Team Square ? On vous déroule une journée type.","Le déroulé d'une journée type","Accueil et petit-déjeuner, temps de travail en salle le matin, déjeuner sur place, puis activités de cohésion l'après-midi : tout s'enchaîne au même endroit. Une interlocutrice unique coordonne la logistique de bout en bout."),
      (("organiser","guide","préparer","preparer"),"Vous organisez {un} {loc} pour la première fois ? Voici le guide pour avancer sereinement.","Organiser sans logistique à gérer","Indiquez vos effectifs, vos dates et vos objectifs : on propose salles, activités et restauration en une formule cohérente. Une interlocutrice unique pilote l'ensemble, de la réservation au jour J."),
      (("demi-journée","demi journee","format court","matinée"),"Une demi-journée suffit-elle pour {un} {loc} ? On vous aide à choisir le bon format.","Demi-journée ou journée complète","Selon vos objectifs et votre budget, on cale une demi-journée (réunion + une activité) ou une journée complète (travail le matin, cohésion l'après-midi, repas inclus). On vous conseille le format le plus efficace pour votre équipe."),
      (("indoor","outdoor","extérieur","exterieur","plein air"),"Indoor ou outdoor pour {un} {loc} ? On combine les deux pour varier les plaisirs de vos équipes.","Indoor et outdoor pour vos équipes","Team Square réunit 7 500 m² indoor et de vastes espaces outdoor : on alterne activités couvertes et plein air selon la saison et vos envies. De quoi proposer un programme varié et adapté à la météo, sans jamais quitter le site."),
      (("réserver","reserver","quand","anticiper"),"Quand réserver {un} {loc} ? Anticiper, surtout en fin d'année, fait toute la différence.","Réserver au bon moment","Les créneaux séminaires partent vite, en particulier au pic de novembre-décembre. Plus vous anticipez, plus vous avez de choix de salle et de dates. Décrivez votre projet et on vous prépare un devis détaillé, valable 30 jours."),
      (("pourquoi","atout","choisir"),"Pourquoi choisir Team Square pour {un} {loc} ? Les atouts d'un lieu unique près de Lille.","Pourquoi Team Square pour vos équipes","Salles de réunion, plus de 22 activités et restauration au même endroit, à 25 minutes de Lille avec parking gratuit. Pas de déplacement entre travail et cohésion, plus de 30 ans d'expérience des responsables, et un interlocuteur unique pour tout coordonner."),
      (("",),"Vous organisez {un} {loc} pour vos équipes ? Team Square réunit salles, activités et restauration au même endroit — de quoi conjuguer travail et cohésion.","Travail et cohésion au même endroit","Sur 7 500 m² à 25 minutes de Lille : salles de réunion équipées, plus de 22 activités pour souder le groupe, un bar et un service de restauration. Tout est réuni pour alterner temps de travail et moments de cohésion."),
    ]}
    _b=ANG[cat]; _x=ANG_EXTRA.get(cat,[])
    ang = _b[:-1] + list(_x) + [_b[-1]]   # extras insérés AVANT l'angle générique
    chosen=ang[-1]
    for keys,intro,h2,pa in ang:
        if keys==("",): continue
        if any(k in tl for k in keys): chosen=(keys,intro,h2,pa); break
    _,intro,h2,pa = chosen
    intro=fmt(intro); h2=fmt(h2); pa=fmt(pa)
    head = intro+"\n\n## "+h2+"\n\n"+pa+" Pour les détails à jour, consultez ["+a1+"]("+TS+fiche+"/).\n\n"+stats+img

    if cat=="loisir":
        rest=("## Comment se déroule une session de "+a+" ?\n\nÀ votre arrivée, un membre de l'équipe vous accueille. Un **animateur dédié** vous explique les règles et les consignes de sécurité, distribue le matériel, puis lance la session. Il rythme le jeu, propose des variantes et veille à ce que chacun trouve sa place. Entre deux temps forts, vous pouvez souffler au bar et enchaîner avec une autre des 22 activités du parc. Pensez au **code TS10** pour −10 % en réservant en ligne.\n\n"+promo_ts10+
            "## Pour quelle occasion ?\n\nLe "+a+" s'adapte à presque toutes les occasions : un anniversaire entre amis ou en famille, un enterrement de vie de garçon ou de jeune fille, une sortie entre collègues, un événement d'entreprise ou CSE, ou tout simplement une sortie du week-end. Selon le groupe, on adapte la formule, la durée et les activités complémentaires.\n\n"+"## Nos conseils pour une sortie réussie\n\nTrois réflexes : **venez à plusieurs** (l'ambiance monte avec le nombre), **réservez à l'avance** — surtout le samedi et pendant les vacances — et **combinez** deux activités pour rythmer la journée. Prévoyez une tenue confortable, arrivez 15 minutes avant le créneau, et n'hésitez pas à appeler l'équipe pour toute question sur l'organisation.\n\n"+"## Pourquoi choisir Team Square\n\nDepuis 2016, le parc accueille plus de 100 000 visiteurs par an et affiche 4,7/5 sur Google. Plus de 22 activités, un animateur dédié par activité, un bar et la restauration sur 7 500 m² à 25 minutes de Lille : tout est réuni au même endroit pour une sortie réussie, du petit groupe à la grande tablée, sans rien à organiser de votre côté. Et avec un parking gratuit et un accès facile depuis Lens, Douai, Arras ou Lille, réunir tout le monde est un jeu d'enfant.\n\n"+access+
            "## Questions fréquentes\n\n**À partir de quel âge peut-on faire le "+a+" ?**  \nL'âge minimum dépend de l'activité ; l'équipe adapte la session à l'âge des participants. En cas de doute, un appel suffit.\n\n**Combien de personnes faut-il au minimum ?**  \nLe "+a+" se réserve dès un petit groupe. Plus vous êtes nombreux, meilleure est l'ambiance.\n\n**Faut-il réserver à l'avance ?**  \nC'est vivement conseillé, surtout le samedi. À moins de 72 h, réservez par téléphone.\n\n**Le "+a+" se pratique-t-il en cas de pluie ?**  \nUne grande partie des activités est en indoor sur 7 500 m², vous êtes à l'abri.\n\n**Comment profiter des −10 % ?**  \nRéservez en ligne avec le **code TS10** et réglez à la réservation, même le samedi.\n\n"+
            "::ts-brief{title=\"📍 En bref\" phone=\"03 74 83 02 02\" cta=\"Réserver en ligne\"}\n- À 25 min de Lille (A1), parking gratuit surveillé\n- Plus de 22 activités au même endroit\n- Animateur dédié + bar et restauration\n- Idéal anniversaire, EVG/EVJF, famille, entreprise\n- −10% en ligne avec le code TS10\n::\n")
    elif cat=="party":
        rest=("## Le pack soirée privatisé pour prolonger la fête\n\nUne fois les activités terminées, beaucoup de groupes choisissent de prolonger avec le **pack soirée privatisé** : une **salle rien que pour vous**, une restauration au choix (cocktail dînatoire, burgers-frites, pizzas ou suprême indien/mexicain), des **tickets boissons** (softs, bières, alcools forts) et le **karaoké** avec ses 25 000 titres. La soirée peut se poursuivre tard dans la nuit, dans un espace privatisé où l'ambiance ne retombe jamais. C'est la formule idéale pour transformer une après-midi d'activités en une soirée dont tout le monde se souviendra. Pensez au **code TS10** pour −10 % sur les activités réservées en ligne.\n\n"+promo_ts10+
            "## Les activités les plus demandées selon l'occasion\n\nLe choix est large : paintball, laser game, bubble foot, lancer de hache, réalité virtuelle, simulateurs F1 et Mirage 2000, cube challenges, babyfoot humain, karaoké et iQuiz. Pour un [EVG]("+TS+"evg-arras-activites-enterrement-vie-garcon/), on privilégie l'action et les défis ; pour un [EVJF]("+TS+"evjf-arras-lens-activites-originales/), un mix d'activités fun et conviviales ; pour un [anniversaire]("+TS+"anniversaire-ado-idees-activites-nord/), on adapte à l'âge du groupe. On peut enchaîner plusieurs activités sur la journée, avec une **tournée de boissons offerte** entre deux activités, le tout encadré par un animateur dédié.\n\n"+
            "## Restauration, boissons et petits plus\n\nCôté restauration, on compose selon vos envies : cocktail dînatoire de 7 bouchées par personne, formule burger ou pizza, ou menu plus complet pour les grandes occasions. Les boissons fonctionnent par tickets ou en libre-service selon la formule. Pour marquer le coup, des **déguisements** et des **tee-shirts personnalisés** sont disponibles pour mettre le héros ou l'héroïne du jour à l'honneur, et vous pouvez apporter votre propre gâteau. Tout est pensé pour que vous n'ayez qu'à profiter.\n\n"+
            "## Comment se passe le jour J\n\nÀ l'arrivée, le chef d'équipe accueille le groupe et présente le programme. Chaque activité démarre par un briefing de sécurité de quelques minutes, puis l'animateur lance le jeu et veille au bon déroulé. Entre deux activités, une pause au bar permet de souffler. Prévoyez d'arriver une quinzaine de minutes avant le créneau, et une tenue confortable adaptée aux activités. À moins de 72 h, la réservation se fait par téléphone pour bien dimensionner l'encadrement.\n\n"+
            "## Nos conseils pour réussir votre événement\n\nRéservez tôt, surtout le samedi et en période de fêtes où les créneaux partent vite. Prévenez du nombre exact de participants pour un encadrement optimal, et **combinez deux activités** pour varier les plaisirs et rythmer la journée. Pensez à la **soirée privatisée** pour prolonger, et aux options déguisements pour l'ambiance. En cas de doute sur la formule la plus adaptée à votre groupe, un simple appel suffit : l'équipe vous conseille.\n\n"+access+
            "## Pourquoi choisir Team Square\n\nTout est réuni au même endroit : plus de 22 activités, une salle privatisable, un bar et la restauration, sur 7 500 m² à 25 minutes de Lille. Depuis 2016, le parc accueille plus de 100 000 visiteurs par an et affiche 4,7/5 sur Google : un cadre rodé pour les groupes, avec un animateur dédié par activité et une équipe habituée aux EVG, EVJF et anniversaires. Vous réservez un créneau, on s'occupe du reste.\n\n"+
            "## Questions fréquentes\n\n**Combien de participants peut-on être ?**  \nDe quelques amis à de grands groupes : on adapte les activités et la privatisation au nombre. Plusieurs formules permettent d'accueillir bien au-delà de la dizaine, en rotation sur les activités.\n\n**Peut-on enchaîner plusieurs activités ?**  \nOui, c'est même recommandé : une **tournée de boissons est offerte** entre deux activités, et la journée n'en est que plus rythmée.\n\n**Y a-t-il une formule soirée ?**  \nOui, un pack soirée privatisé (salle + restauration + boissons + karaoké) prolonge la fête, tard dans la nuit.\n\n**Peut-on apporter son gâteau et des déguisements ?**  \nLe gâteau est autorisé, et des déguisements comme des tee-shirts personnalisés sont disponibles sur place.\n\n**Comment profiter des −10 % ?**  \nRéservez vos activités en ligne avec le **code TS10**, paiement à la réservation, offre valable même le samedi.\n\n**Faut-il réserver à l'avance ?**  \nOui, surtout le samedi et en période de fêtes. À moins de 72 h, la réservation se fait par téléphone.\n\n"+
            "::ts-brief{title=\"📍 En bref\" phone=\"03 74 83 02 02\" cta=\"Réserver en ligne\"}\n- Plus de 22 activités + soirée privatisable\n- À 25 min de Lille (A1), parking gratuit\n- Animateur dédié, bar et restauration\n- Tournée offerte entre deux activités\n- −10% en ligne avec le code TS10\n::\n")
    elif cat=="venue":
        rest=("## Traiteur, boissons et menu oriental\n\nNotre cuisine maison propose une carte traiteur complète pour composer votre repas à la carte : **apéritifs et cocktails dînatoires**, buffets froids (crudités, charcuteries, viandes), plats traditionnels chauds, et un **menu oriental 100 % Halal** sur demande (chorba, tajines, couscous, pastillas). Côté boissons, softs, bières, vins et champagnes sont disponibles, en libre-service ou au ticket selon la formule. Dès que le traiteur et les boissons sont pris chez nous, la **vaisselle et la verrerie sont incluses** — un poste de moins à gérer. On adapte les quantités et les menus à votre nombre d'invités et à vos convives.\n\n"+promo_devis+
            "## La coordination, du devis au jour J\n\nDès la signature, une **coordinatrice événementielle** prend le relais et vous accompagne jusqu'au bout. Un **rendez-vous a lieu 15 jours avant** l'événement pour tout figer : menus, planning détaillé (déco, accueil, apéritif, entrée, plat, fromage, dessert), agencement de la salle et mobilier (tables rondes ou rectangulaires, mange-debout, vidéoprojecteur, sonorisation). Le jour J, vous êtes accueilli et guidé, et grâce à un membre **d'astreinte**, votre réception peut se prolonger **jusqu'à 5 h du matin**, n'importe quel jour de la semaine.\n\n"+
            "## Capacités et configurations des salles\n\nTeam Square Events dispose de plusieurs salles privatisées, **de 20 à 200 personnes**, modulables selon le format de votre événement : repas assis, cocktail debout, ou configuration mixte. Chaque espace est équipé (tables, chaises, vidéoprojecteur, sonorisation simple), et vous êtes libre de la décoration, avec une installation possible la veille selon disponibilité. On vous oriente vers la salle la mieux adaptée à votre nombre d'invités et à l'ambiance recherchée.\n\n"+
            "## Réservation, acompte et conditions\n\nLa réservation se confirme par un **acompte de 30 %** à la signature du devis, qui reste **valable 30 jours**. Le solde se règle avant l'événement, et les éventuelles dépenses supplémentaires sont facturées peu après. Un chèque de caution est demandé et restitué après l'événement s'il n'y a pas de dégât. Tout est cadré clairement dès le devis, pour avancer sereinement et sans surprise.\n\n"+
            "## Nos conseils d'organisation\n\nRéservez tôt — les samedis et la période de fin d'année partent très vite. Soignez le nombre d'invités au plus juste, le choix du menu selon vos convives, et anticipez la décoration. Profitez du **rendez-vous des 15 jours** pour valider chaque poste de votre événement. Et n'hésitez pas à poser vos questions en amont : l'équipe est là pour vous guider à chaque étape.\n\n"+access+
            "## Pourquoi choisir Team Square Events\n\nUn lieu unique qui réunit salle privatisée, traiteur maison et coordination, à 25 minutes de Lille avec un parking gratuit et surveillé. Depuis 2016, l'équipe organise des dizaines de réceptions par an, y compris des prestations orientales 100 % Halal, et reste votre interlocuteur unique du devis jusqu'au jour J. Vous gagnez en sérénité : un seul contact, un devis clair, et une fête qui peut se prolonger jusqu'à 5 h du matin.\n\n"+
            "## Questions fréquentes\n\n**Quelle est la capacité des salles ?**  \nDe 20 à 200 personnes selon la salle. On vous oriente vers l'espace le mieux adapté à votre nombre d'invités et au format (repas assis ou cocktail).\n\n**Peut-on apporter son propre traiteur ?**  \nLa formule clé en main suppose une restauration Team Square. Sinon, la salle se loue seule. L'équipe vous explique les deux options sur devis.\n\n**Jusqu'à quelle heure peut-on faire la fête ?**  \nGrâce à un membre d'astreinte, l'événement peut se prolonger jusqu'à 5 h du matin, n'importe quel jour de la semaine.\n\n**Comment réserver et quel acompte ?**  \nUn acompte de 30 % valide la réservation après acceptation du devis (valable 30 jours) ; le solde se règle avant l'événement.\n\n**La vaisselle est-elle incluse ?**  \nOui, dès que le traiteur et les boissons sont pris chez nous, la vaisselle et la verrerie sont comprises.\n\n**Les animaux sont-ils acceptés ?**  \nIls sont tolérés dans la salle privatisée (espace privé loué). Les chiens d'assistance sont toujours admis.\n\n"+
            "::ts-brief{title=\"📍 En bref\" phone=\"03 74 83 02 02\" cta=\"Demander un devis\"}\n- Salles de 20 à 200 personnes, privatisées\n- Traiteur maison + menu oriental Halal\n- Formule clé en main ou location seule\n- Fête possible jusqu'à 5 h du matin\n- À 25 min de Lille (A1), parking gratuit\n::\n")
    else:
        rest=("## Salles de réunion et équipements\n\nTeam Square met à disposition des **salles de réunion équipées** (vidéoprojecteur, sonorisation, configuration en U, théâtre ou îlots), modulables de la petite équipe au grand groupe, en forfait demi-journée ou journée. Elles se trouvent au même endroit que les activités et la restauration, sur un site de 7 500 m² à 25 minutes de Lille : vos collaborateurs passent du temps de travail aux temps de cohésion **sans le moindre déplacement**. Pour les grands événements d'entreprise, des espaces peuvent accueillir plusieurs centaines de personnes.\n\n"+promo_devis+
            "## Des activités de team building sur mesure\n\nOlympiades, escape game, paintball, laser game, bubble foot, simulateurs, réalité virtuelle, babyfoot humain… on sélectionne avec vous les activités les plus adaptées à vos **objectifs** : renforcer la cohésion, fluidifier la communication, apprendre à gérer le stress ou simplement décompresser ensemble. Chaque activité est encadrée par un animateur dédié, et l'on peut composer un parcours qui alterne défis collectifs et moments plus détendus. Le tout se combine avec la salle de réunion pour une journée cohérente.\n\n"+
            "## La formule séminaire tout inclus\n\nPour simplifier l'organisation et la facturation, la **formule séminaire tout inclus** réunit petit-déjeuner d'accueil, salle de réunion, déjeuner sur place et activités de mise en pratique, à partir de 5 personnes. Les thématiques peuvent porter sur la cohésion d'équipe, l'optimisation des performances, la prévention santé, la gestion du stress ou des conflits, ou la communication interne. Une seule formule, un seul interlocuteur, zéro logistique à gérer de votre côté.\n\n"+
            "## Restauration et coordination\n\nPause petit-déjeuner, déjeuner sur place, cocktail de clôture : notre cuisine compose des formules adaptées à votre journée, avec **menu oriental Halal sur demande**. Tout est sur place, pour ne pas couper le rythme. Une **interlocutrice unique** coordonne l'ensemble, de la réservation au jour J, et reste votre contact tout au long de l'organisation. Pensez à réserver à l'avance, en particulier au pic de novembre-décembre où les créneaux séminaires partent vite.\n\n"+
            "## Nos conseils d'organisation\n\nAnticipez surtout en fin d'année, **définissez vos objectifs** (cohésion, communication, détente) pour cibler les bonnes activités, et prévoyez un bon équilibre entre temps de travail et temps de cohésion. Indiquez vos effectifs et vos contraintes dès le départ : l'équipe bâtit une proposition cohérente et un devis clair. Un séminaire bien préparé, c'est une journée fluide et des équipes qui en ressortent soudées.\n\n"+access+
            "## Pourquoi choisir Team Square pour vos équipes\n\nUn site unique à 25 minutes de Lille qui combine salles de réunion, plus de 22 activités de cohésion et restauration, sans déplacement entre les séquences de la journée. Les responsables cumulent plus de 30 ans d'expérience, et de nombreuses entreprises de la région font confiance au parc pour leurs séminaires et team buildings. Un seul interlocuteur coordonne l'ensemble, pour une journée fluide et des équipes qui en ressortent soudées.\n\n"+
            "## Questions fréquentes\n\n**Combien de participants peut-on accueillir ?**  \nDe petites équipes à plusieurs centaines de personnes, selon les salles et les activités. Tout se dimensionne sur devis.\n\n**Peut-on combiner réunion et activités ?**  \nOui, c'est l'intérêt du lieu : salle de réunion le matin, activités de cohésion l'après-midi, le tout sans déplacement.\n\n**Y a-t-il une formule tout inclus ?**  \nOui, la formule séminaire (petit-déjeuner + salle + déjeuner + activités) à partir de 5 personnes simplifie l'organisation et la facturation.\n\n**Quelles thématiques de team building proposez-vous ?**  \nCohésion d'équipe, performance, prévention santé, gestion du stress et des conflits, communication interne — on adapte aux enjeux de votre équipe.\n\n**Comment obtenir un tarif ?**  \nDécrivez-nous votre projet (effectifs, dates, objectifs) : on prépare un devis détaillé, valable 30 jours.\n\n**Quand réserver ?**  \nLe plus tôt possible, surtout en fin d'année où les créneaux séminaires partent vite.\n\n"+
            "::ts-brief{title=\"📍 En bref\" phone=\"03 74 83 02 02\" cta=\"Demander un devis\"}\n- Salles de réunion + 22 activités au même endroit\n- Formule séminaire tout inclus dès 5 personnes\n- Team building encadré par des animateurs\n- Restauration sur place, menu Halal sur demande\n- À 25 min de Lille (A1), parking gratuit\n::\n")
    return _el(fm + head + rest, a)

def run(cmd, cwd=None): return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
def log(msg):
    open(LOG,"a",encoding="utf-8").write(f"{datetime.datetime.now().isoformat()}  {msg}\n"); print(msg)
def save(rows, fn):
    tmp=RESERVOIR+".tmp"; w=csv.DictWriter(open(tmp,"w",encoding="utf-8",newline=""),fieldnames=fn); w.writeheader(); w.writerows(rows); os.replace(tmp,RESERVOIR)
def gen_topics(act, ville):
    L = "dans les Hauts-de-France" if ville.strip().lower().startswith("les ") else "à "+ville
    aL = act.lower()
    UNMAP={"EVG":"un EVG","EVJF":"un EVJF","Enterrement de vie de célibataire":"un enterrement de vie de célibataire","Anniversaire":"un anniversaire",
     "Mariage":"un mariage","Baptême":"un baptême","Communion":"une communion","Espace de réception":"une réception","Location de salles":"une location de salle",
     "Séminaire":"un séminaire","Team Building":"un team building"}
    un = UNMAP.get(act, "un "+aL)
    CATB={"Séminaire":"b2b","Team Building":"b2b","EVG":"party","EVJF":"party","Enterrement de vie de célibataire":"party","Anniversaire":"party",
     "Mariage":"venue","Baptême":"venue","Communion":"venue","Espace de réception":"venue","Location de salles":"venue"}
    cat=CATB.get(act,"loisir")
    P={
    "loisir":["{ACT} {loc} : combien ça coûte ? Tarifs et formules 2026","Que faire {loc} ce week-end ? Essayez le {act}","{ACT} {loc} : à partir de quel âge et combien de joueurs ?","Organiser un anniversaire {act} {loc} : le guide complet","{ACT} {loc} pour un EVG ou un EVJF entre amis","Jour de pluie {loc} ? Le {act} en salle est la solution","{ACT} {loc} entre collègues : team building et cohésion","Idée cadeau {loc} : offrir une séance de {act}","{ACT} {loc} : première fois, nos conseils pour débuter","{ACT} {loc} en famille : une sortie pour petits et grands","{ACT} {loc} : combien de temps prévoir pour une séance ?","{ACT} {loc} : la sortie idéale pour un grand groupe","{ACT} {loc} : indoor ou outdoor, on vous explique","{ACT} {loc} : sécurité et encadrement, ce qu'il faut savoir","{ACT} {loc} : prolonger la journée après l'activité","{ACT} {loc} : accès et trajet depuis toute la région","{ACT} {loc} : la sortie CSE qui plaît à tous","{ACT} {loc} pour un groupe scolaire ou un centre de loisirs","{ACT} {loc} : une sortie pour toutes les saisons","{ACT} {loc} : quelle tenue et que prévoir ?","{ACT} {loc} : du curieux au confirmé, quel niveau ?","{ACT} {loc} : nos astuces pour réussir votre sortie de groupe"],
    "party":["{ACT} {loc} : combien ça coûte ? Budget et formules","{ACT} {loc} : nos meilleures idées d'activités","{ACT} {loc} : le programme d'une journée réussie","{ACT} {loc} : la soirée privatisée pour finir en beauté","{ACT} {loc} : combien de participants prévoir ?","Jour de pluie {loc} ? {ACT} reste au sec en salle","Organiser {un} {loc} : le guide complet","{ACT} {loc} : surprendre le groupe, nos astuces originales","{ACT} {loc} pas cher : nos bons plans","{ACT} {loc} : déguisements et options pour le héros du jour","{ACT} {loc} : une fête pour tous les âges","{ACT} {loc} : combien de temps prévoir ?","{ACT} {loc} : quand réserver pour être sûr de sa date ?","Restauration pour {un} {loc} : burgers, cocktail ou menu ?","{ACT} {loc} : nos conseils pour un événement réussi"],
    "venue":["{ACT} {loc} : combien ça coûte ? Tarifs et formules","{ACT} {loc} : combien d'invités peut-on accueillir ?","Traiteur pour {un} {loc} : nos formules","Décoration et aménagement pour {un} {loc}","{ACT} {loc} : le déroulé d'une réception type","Réserver une salle pour {un} {loc} : mode d'emploi","{ACT} {loc} : location seule ou formule tout inclus ?","{ACT} {loc} : jusqu'à quelle heure faire la fête ?","Organiser {un} {loc} : le guide complet","Boissons pour {un} {loc} : softs, vins et champagnes","{ACT} {loc} : comment occuper les enfants ?","{ACT} {loc} : acompte, devis et conditions","{ACT} {loc} : quelle période choisir pour votre événement ?","{ACT} {loc} : nos conseils d'organisation"],
    "b2b":["{ACT} {loc} : combien ça coûte ? Tarifs et formules","{ACT} {loc} : quelles activités de cohésion ?","{ACT} {loc} : nos salles de réunion équipées","{ACT} {loc} : combien de participants peut-on accueillir ?","{ACT} {loc} : la formule séminaire tout inclus","{ACT} {loc} : restauration et traiteur sur place","{ACT} {loc} : quels objectifs pour votre équipe ?","{ACT} {loc} : le déroulé d'une journée type","Organiser {un} {loc} : le guide complet","{ACT} {loc} : demi-journée ou journée complète ?","{ACT} {loc} : indoor ou outdoor pour vos équipes ?","{ACT} {loc} : quand réserver pour votre séminaire ?","{ACT} {loc} : pourquoi choisir Team Square ?","{ACT} {loc} : tout ce qu'il faut savoir pour vos équipes"],
    }
    allt = P[cat] + list(TOPICS_EXTRA.get(cat, []))
    base=[_el(t.replace("{ACT}",act).replace("{act}",aL).replace("{loc}",L).replace("{un}",un), aL) for t in allt]
    return base

def topup_reservoir(rows, target=10):
    from collections import Counter, defaultdict
    info={}; used=defaultdict(set); todo=Counter()
    for r in rows:
        info[r["repo"]]=(r["domaine"],r["ville"],r["activite"])
        used[r["repo"]].add(r["titre"].strip().lower())
        if r["statut"]=="todo": todo[r["repo"]]+=1
    added=0
    for repo,(dom,ville,act) in info.items():
        if todo[repo]>=target: continue
        cands=gen_topics(act, ville)
        # variantes de secours si le pool de base est épuisé
        extra=[c+" — édition 2026" for c in cands]+[c+" : nos réponses" for c in cands]
        for t in cands+extra:
            if todo[repo]>=target: break
            if t.strip().lower() in used[repo]: continue
            rows.append({"repo":repo,"domaine":dom,"ville":ville,"activite":act,"titre":t,"statut":"todo"})
            used[repo].add(t.strip().lower()); todo[repo]+=1; added+=1
    return added

_STOP=set("le la les l un une de des du d a au aux dans pour nos notre votre vos et ou en ce cette son sa ses on vous il elle qui que quoi sur se s y t n est sont avec sans plus moins votre".split())
def _angle_sig(title, act, ville):
    t=title.lower()
    for x in [act.lower(), ville.lower(), "hauts-de-france", "hauts de france"]:
        t=t.replace(x," ")
    words=[w for w in re.split(r"[^a-zàâäéèêëîïôöûüç]+", t) if len(w)>1 and w not in _STOP]
    return frozenset(words)

def reorder_todo(rows):
    from collections import Counter
    head=[r for r in rows if r.get("statut","").strip()!="todo"]
    todo=[r for r in rows if r.get("statut","").strip()=="todo"]
    sig={id(r):_angle_sig(r["titre"],r["activite"],r["ville"]) for r in todo}
    rem=todo[:]; out=[]; prev=None; recent=[]
    def ok(r,relax):
        if prev is None: return True
        if relax<4 and r["activite"]==prev["activite"]: return False
        if relax<3 and r["ville"]==prev["ville"]: return False
        if relax<2 and sig[id(r)] in recent[-3:]: return False   # pas le meme angle sur 3 derniers
        if relax<1 and (sig[id(r)] in recent[-5:] or r["ville"] in [x["ville"] for x in out[-2:]]): return False
        return True
    while rem:
        chosen=None
        for relax in range(5):
            pool=[r for r in rem if ok(r,relax)]
            if pool:
                cnt=Counter(r["activite"] for r in rem)
                pool.sort(key=lambda r:-cnt[r["activite"]])
                chosen=pool[0]; break
        if chosen is None: chosen=rem[0]
        out.append(chosen); rem.remove(chosen); prev=chosen; recent.append(sig[id(chosen)])
    return head+out

def main():
    tok=open(TOKEN_FILE,encoding="utf-8").read().strip().splitlines()[0].strip()
    rows=list(csv.DictReader(open(RESERVOIR,encoding="utf-8"))); fn=rows[0].keys()
    todo=[r for r in rows if r["statut"]=="todo"][:N]
    if not todo: log("Aucun sujet todo restant — recharger le réservoir."); return
    log(f"Run: publication de {len(todo)} article(s)."); pub=0
    for p in todo:
        repo,city,act,title=p["repo"],p["ville"],p["activite"],p["titre"]
        loc="dans les Hauts-de-France" if city.startswith("les ") else f"à {city}"
        url=f"https://x-access-token:{tok}@github.com/{ORG}/{repo}.git"; wd=tempfile.mkdtemp(); ok=False
        try:
            if run(["git","clone","--depth","1","-q",url,wd]).returncode!=0: log(f"  ECHEC clone {repo}")
            else:
                run(["git","config","user.email","teamsquare.ai@gmail.com"],cwd=wd); run(["git","config","user.name","auto-blog"],cwd=wd)
                bd=os.path.join(wd,"content","blog"); nums=[int(m.group(1)) for f in os.listdir(bd) if (m:=re.match(r"article-(\d+)\.md$",f))]
                nxt=(max(nums)+1) if nums else 1
                used=used_images(os.path.join(wd,"content"))
                cov,im2=pick_images(os.path.join(wd,"public","img"),PREFIX.get(act,"pb"),used)
                open(os.path.join(bd,f"article-{nxt}.md"),"w",encoding="utf-8").write(article_md(title,loc,act,cov,im2))
                run(["git","add","-A"],cwd=wd)
                if run(["git","commit","-q","-m",f"Article auto: {title}"],cwd=wd).returncode==0 and run(["git","push","-q","origin","HEAD"],cwd=wd).returncode==0:
                    ok=True; log(f"  OK {repo} -> article-{nxt}")
                else: log(f"  ECHEC push {repo}")
        finally: shutil.rmtree(wd,ignore_errors=True)
        if ok: p["statut"]="done"; save(rows,fn); pub+=1
    log(f"Run terminé : {pub} publié(s).")
    n_add=topup_reservoir(rows)
    rows=reorder_todo(rows)
    save(rows,fn)
    if n_add: log(f"Réservoir réalimenté : +{n_add} sujet(s) pour rester à 10/site.")
    log("Réservoir réordonné (anti-répétition ville/activité/angle).")
if __name__=="__main__": main()
