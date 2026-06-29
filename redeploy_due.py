#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
redeploy_due.py — pour chaque article du calendrier dont la date est ARRIVÉE
(date <= maintenant) et pas encore "deployed", redéploie le site concerné
(mini-commit poussé -> Vercel reconstruit -> index+sitemap rafraîchis -> article visible).
Un seul redéploiement par site et par run (dédoublonné). Idempotent via le statut.

Token GitHub : variable d'env GH_TOKEN (cron) sinon jeton-github.txt (local).
Usage : python3 redeploy_due.py [--dry-run]
"""
import csv, os, sys, datetime, tempfile, shutil
BASE=os.path.dirname(os.path.abspath(__file__))
ORG="TS-TeamSquare"
CAL=os.path.join(BASE,"calendrier-publication.csv")
TOKEN_FILE=os.path.join(BASE,"jeton-github.txt")
import subprocess
def run(cmd,cwd=None): return subprocess.run(cmd,cwd=cwd,capture_output=True,text=True)

def token():
    t=os.environ.get("GH_TOKEN") or os.environ.get("GH_PAT")
    if t: return t.strip()
    return open(TOKEN_FILE,encoding="utf-8").read().strip().splitlines()[0].strip()

def main(dry):
    if not os.path.exists(CAL):
        print("calendrier-publication.csv introuvable — rien à faire."); return
    rows=list(csv.DictReader(open(CAL,encoding="utf-8")))
    fn=list(rows[0].keys())
    now=datetime.datetime.now(datetime.timezone.utc)
    due_repos={}   # repo -> liste des lignes échues à marquer deployed
    for r in rows:
        if r["statut"]=="deployed": continue
        try: d=datetime.datetime.fromisoformat(r["date"].replace("Z","+00:00"))
        except Exception: continue
        if d<=now:
            due_repos.setdefault(r["repo"],[]).append(r)
    if not due_repos:
        print(f"[{now:%Y-%m-%d %H:%M}Z] Aucun site échu. RAS."); return
    print(f"[{now:%Y-%m-%d %H:%M}Z] Sites échus à redéployer : {len(due_repos)}")
    if dry:
        for repo,ls in due_repos.items():
            print(f"  DRY {repo} <- {len(ls)} article(s) dû(s) : {[l['article'] or l['titre'][:30] for l in ls]}")
        print("DRY-RUN : aucun push.")
        return
    tok=token()
    for repo,ls in due_repos.items():
        url=f"https://x-access-token:{tok}@github.com/{ORG}/{repo}.git"; wd=tempfile.mkdtemp()
        try:
            if run(["git","clone","--depth","1","-q",url,wd]).returncode!=0:
                print(f"  ECHEC clone {repo}"); continue
            run(["git","config","user.email","teamsquare.ai@gmail.com"],cwd=wd)
            run(["git","config","user.name","auto-blog"],cwd=wd)
            msg=f"redeploy: publication due ({datetime.date.today().isoformat()}) [{len(ls)} art.]"
            ok=(run(["git","commit","--allow-empty","-q","-m",msg],cwd=wd).returncode==0
                and run(["git","push","-q","origin","HEAD"],cwd=wd).returncode==0)
            if ok:
                for l in ls: l["statut"]="deployed"
                print(f"  OK redeploy {repo}")
            else: print(f"  ECHEC push {repo}")
        finally: shutil.rmtree(wd,ignore_errors=True)
    tmp=CAL+".tmp"
    w=csv.DictWriter(open(tmp,"w",encoding="utf-8",newline=""),fieldnames=fn); w.writeheader(); w.writerows(rows)
    os.replace(tmp,CAL)
    print("Calendrier mis à jour (statuts deployed).")

if __name__=="__main__":
    main("--dry-run" in sys.argv)
