#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
planifier.py — assigne à CHAQUE SITE un créneau JOUR+HEURE UNIQUE (aucune collision
entre les 82 sites) et une DATE DE PUBLICATION FUTURE par article (cadence hebdo),
puis écrit calendrier-publication.csv. Optionnel : --push pousse les articles datés-futur.

Créneau unique par site i (repos triés) :
  jour_offset = i % 7            -> réparti sur 7 jours (~12 sites/jour)
  heure       = 8 + (i // 7)     -> 8h..19h, une heure différente par site le même jour
  minute      = (i*7) % 60       -> décalage fin, aspect organique
=> (jour, heure) est unique pour chaque site (bijection, 82 < 7*12=84).
Le cron de révélation doit tourner au moins TOUTES LES HEURES pour respecter ces heures.

Usage :
  python3 planifier.py                 # DRY-RUN : calcule créneaux + calendrier, ne pousse rien
  python3 planifier.py --push [N]      # pousse jusqu'à N articles datés-futur (défaut: tous les planned)
Options : --interval J (défaut 7) | --start AAAA-MM-JJ (défaut aujourd'hui+3)
"""
import csv, os, sys, datetime, tempfile, shutil, re, argparse
BASE=os.path.dirname(os.path.abspath(__file__))
sys.argv_backup=sys.argv[:]; sys.argv=[sys.argv[0]]
sys.path.insert(0, BASE)
import publisher as P
sys.argv=sys.argv_backup
RES=os.path.join(BASE,"reservoir-articles.csv")
if not os.path.exists(RES): RES=os.path.join(BASE,"..","reservoir-articles.csv")
CAL=os.path.join(BASE,"calendrier-publication.csv")
if not os.path.exists(CAL): CAL=os.path.join(BASE,"..","calendrier-publication.csv")

def parse_args():
    ap=argparse.ArgumentParser()
    ap.add_argument("--push",nargs="?",const=-1,type=int,default=None)
    ap.add_argument("--interval",type=int,default=7)
    ap.add_argument("--start",default=None)
    return ap.parse_args()

def slot(i):
    """(jour_offset, heure, minute) unique par site."""
    return i % 7, 8 + (i // 7), (i*7) % 60

def load_cal():
    if not os.path.exists(CAL): return []
    return list(csv.DictReader(open(CAL,encoding="utf-8")))

def save_cal(rows):
    fn=["date","repo","domaine","ville","activite","titre","article","statut"]
    if len(rows) < 100:
        print(f"ABORT save_cal: calendrier suspect ({len(rows)} lignes <100) — écriture annulée"); return
    tmp=CAL+".tmp"
    w=csv.DictWriter(open(tmp,"w",encoding="utf-8",newline=""),fieldnames=fn)
    w.writeheader()
    for r in rows: w.writerow({k:r.get(k,"") for k in fn})
    os.replace(tmp,CAL)

def plan(args):
    rows=list(csv.DictReader(open(RES,encoding="utf-8")))
    todos={}
    for r in rows:
        if r["statut"].strip()=="todo":
            todos.setdefault(r["repo"],[]).append(r)
    repos=sorted(todos.keys())
    start = datetime.date.fromisoformat(args.start) if args.start else (datetime.date.today()+datetime.timedelta(days=3))
    cal=load_cal()
    already={(c["repo"],c["titre"].strip()) for c in cal}
    last={}
    for c in cal:
        d=datetime.date.fromisoformat(c["date"][:10])
        if c["repo"] not in last or d>last[c["repo"]]: last[c["repo"]]=d
    new=[]; slotmap={}
    for i,repo in enumerate(repos):
        day,hh,mm=slot(i); slotmap[repo]=(day,hh,mm)
        base=start+datetime.timedelta(days=day)
        k=0
        if repo in last:
            while base+datetime.timedelta(days=k*args.interval) <= last[repo]: k+=1
        for r in todos[repo]:
            if (repo,r["titre"].strip()) in already: continue
            d=base+datetime.timedelta(days=k*args.interval)
            stamp=f"{d.isoformat()}T{hh:02d}:{mm:02d}:00.000Z"
            new.append({"date":stamp,"repo":repo,"domaine":r["domaine"],"ville":r["ville"],
                        "activite":r["activite"],"titre":r["titre"],"article":"","statut":"planned"})
            k+=1
    allcal=cal+new
    allcal.sort(key=lambda c:(c["date"],c["repo"]))
    save_cal(allcal)
    return new, allcal, slotmap

def token():
    t=os.environ.get("GH_TOKEN") or os.environ.get("GH_PAT")
    if t: return t.strip()
    return open(P.TOKEN_FILE,encoding="utf-8").read().strip().splitlines()[0].strip()

def push_planned(allcal, limit):
    tok=token()
    todo=[c for c in allcal if c["statut"]=="planned"]
    if limit and limit>0: todo=todo[:limit]
    done=0
    for c in todo:
        repo=c["repo"]; title=c["titre"]; act=c["activite"]; city=c["ville"]
        loc="dans les Hauts-de-France" if city.startswith("les ") else f"à {city}"
        url=f"https://x-access-token:{tok}@github.com/{P.ORG}/{repo}.git"; wd=tempfile.mkdtemp()
        try:
            if P.run(["git","clone","--depth","1","-q",url,wd]).returncode!=0:
                print(f"  ECHEC clone {repo}"); continue
            P.run(["git","config","user.email","teamsquare.ai@gmail.com"],cwd=wd)
            P.run(["git","config","user.name","auto-blog"],cwd=wd)
            bd=os.path.join(wd,"content","blog")
            nums=[int(m.group(1)) for f in os.listdir(bd) if (m:=re.match(r"article-(\d+)\.md$",f))]
            nxt=(max(nums)+1) if nums else 1
            used=P.used_images(os.path.join(wd,"content"))
            cov,im2=P.pick_images(os.path.join(wd,"public","img"),P.PREFIX.get(act,"pb"),used)
            md=P.article_md(title,loc,act,cov,im2)
            md=re.sub(r"date: .*?\n", f"date: {c['date']}\n", md, count=1)
            open(os.path.join(bd,f"article-{nxt}.md"),"w",encoding="utf-8").write(md)
            P.run(["git","add","-A"],cwd=wd)
            ok=(P.run(["git","commit","-q","-m",f"Article planifié ({c['date'][:16]}): {title}"],cwd=wd).returncode==0
                and P.run(["git","push","-q","origin","HEAD"],cwd=wd).returncode==0)
            if ok:
                c["statut"]="pushed"; c["article"]=f"article-{nxt}"; done+=1
                print(f"  OK {repo} -> article-{nxt} (visible le {c['date'][:16]})")
            else: print(f"  ECHEC push {repo}")
        finally: shutil.rmtree(wd,ignore_errors=True)
    return done

if __name__=="__main__":
    args=parse_args()
    new,allcal,slotmap=plan(args)
    print(f"Planifié (nouveaux créneaux) : {len(new)} | calendrier total : {len(allcal)} lignes")
    # contrôle d'unicité des créneaux (jour, heure)
    seen={}; coll=0
    for repo,(d,h,m) in slotmap.items():
        key=(d,h)
        if key in seen: coll+=1
        seen.setdefault(key,[]).append(repo)
    print(f"Créneaux (jour,heure) uniques : {len(seen)} pour {len(slotmap)} sites | collisions: {coll}")
    if args.push is not None:
        done=push_planned(allcal, args.push); save_cal(allcal)
        print(f"Articles datés-futur poussés : {done}")
    else:
        print("DRY-RUN : aucun push.")
