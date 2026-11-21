#!/usr/bin/env python3
"""Publica o post do dia de @luanabuzolin.rh pela API oficial do Instagram (Instagram API with Instagram Login).

Uso (no GitHub Actions):
  python3 scripts/publish.py                 # publica o post de hoje se já chegou a hora (15 min de tolerância)
  python3 scripts/publish.py --dia 2026-11-23 --agora   # força um dia específico, ignorando a hora
  python3 scripts/publish.py --refresh-token

Secrets/variáveis: IG_ACCESS_TOKEN, IG_USER_ID, PAGES_BASE (ex.: https://pedro-nascimento-line.github.io/luana-rh),
IG_API_HOST opcional ("graph.instagram.com", padrão).

Regras: nunca publica duas vezes (confere meta.json); dia sem pasta em posts/ não é erro (qua, sáb e dom não têm post);
espera as imagens estarem no Pages; tenta 3 vezes com 5 min de intervalo; grava tudo em log/publicacoes.csv.
"""
import argparse, csv, datetime as dt, json, os, sys, time
from pathlib import Path
from zoneinfo import ZoneInfo
import requests

HOST = (os.environ.get("IG_API_HOST") or "graph.instagram.com").strip()
API = f"https://{HOST}/v21.0"
RAIZ = Path(__file__).resolve().parent.parent
BRT = ZoneInfo("America/Sao_Paulo")
TOKEN = os.environ.get("IG_ACCESS_TOKEN", "")
USER = os.environ.get("IG_USER_ID", "")
BASE = os.environ.get("PAGES_BASE", "").rstrip("/")


def log(dia, tipo, ig_id, status, erro=""):
    agora = dt.datetime.now(BRT)
    with open(RAIZ / "log/publicacoes.csv", "a", newline="") as f:
        csv.writer(f).writerow([agora.date().isoformat(), agora.strftime("%H:%M"), dia, tipo, ig_id, status, erro[:200]])


def api(method, path, **params):
    params["access_token"] = TOKEN
    r = requests.request(method, f"{API}/{path}", params=params, timeout=60)
    try:
        data = r.json()
    except ValueError:
        data = {"raw": r.text}
    if r.status_code >= 400 or "error" in data:
        raise RuntimeError(f"{path}: {data.get('error', data)}")
    return data


def esperar_container(cid, timeout=300):
    t0 = time.time()
    while time.time() - t0 < timeout:
        st = api("GET", cid, fields="status_code,status")
        if st.get("status_code") == "FINISHED":
            return
        if st.get("status_code") == "ERROR":
            raise RuntimeError(f"container {cid} com erro: {st.get('status')}")
        time.sleep(8)
    raise RuntimeError(f"container {cid} não finalizou em {timeout}s")


def url_ok(url, tentativas=30, intervalo=30):
    for _ in range(tentativas):
        try:
            if requests.head(url, timeout=20).status_code == 200:
                return True
        except requests.RequestException:
            pass
        time.sleep(intervalo)
    return False


def montar_legenda(pasta):
    legenda = (pasta / "legenda.txt").read_text().strip()
    cred = pasta / "credito.txt"
    if cred.exists():
        legenda += "\n\n" + cred.read_text().strip()
    hp = pasta / "hashtags.txt"
    tags = hp.read_text().split() if hp.exists() else []
    while tags and len(legenda) + 4 + len(" ".join(tags)) > 2200:
        tags.pop()
    if tags:
        legenda += "\n\n" + " ".join(tags)
    if len(legenda) > 2200:
        raise RuntimeError(f"legenda com {len(legenda)} caracteres (limite 2200)")
    return legenda


def publicar(dia, pasta, meta):
    cards = sorted(p.name for p in pasta.glob("card_*.jpg"))
    if not cards:
        raise RuntimeError("nenhum card_*.jpg na pasta do post")
    if len(cards) > 10:
        raise RuntimeError("carrossel com mais de 10 cards")
    legenda = montar_legenda(pasta)
    urls = [f"{BASE}/posts/{dia}/{c}" for c in cards]
    for u in urls:
        if not url_ok(u):
            raise RuntimeError(f"imagem não acessível no Pages: {u}")
    if len(urls) == 1:
        cont = api("POST", f"{USER}/media", image_url=urls[0], caption=legenda)
    else:
        filhos = []
        for u in urls:
            c = api("POST", f"{USER}/media", image_url=u, is_carousel_item="true")
            esperar_container(c["id"]); filhos.append(c["id"])
        cont = api("POST", f"{USER}/media", media_type="CAROUSEL", children=",".join(filhos), caption=legenda)
    esperar_container(cont["id"])
    pub = api("POST", f"{USER}/media_publish", creation_id=cont["id"])
    meta["feed_id"] = pub["id"]
    try:
        meta["permalink"] = api("GET", pub["id"], fields="permalink").get("permalink", "")
    except Exception:
        pass
    log(dia, "carrossel" if len(urls) > 1 else "post", pub["id"], "ok")


def refresh_token():
    if HOST != "graph.instagram.com":
        print(TOKEN); return
    d = requests.get("https://graph.instagram.com/refresh_access_token",
                     params={"grant_type": "ig_refresh_token", "access_token": TOKEN}, timeout=60).json()
    if "access_token" not in d:
        raise RuntimeError(f"refresh falhou: {d}")
    print(d["access_token"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dia", default=dt.datetime.now(BRT).date().isoformat())
    ap.add_argument("--agora", action="store_true", help="ignora o horário do post")
    ap.add_argument("--refresh-token", action="store_true")
    a = ap.parse_args()
    if a.refresh_token:
        return refresh_token()
    if not (TOKEN and USER and BASE):
        sys.exit("faltam IG_ACCESS_TOKEN, IG_USER_ID ou PAGES_BASE")
    pasta = RAIZ / "posts" / a.dia
    if not (pasta / "post.json").exists():
        print(f"sem post para {a.dia}"); return
    post = json.loads((pasta / "post.json").read_text())
    meta_p = pasta / "meta.json"
    meta = json.loads(meta_p.read_text()) if meta_p.exists() else {}
    if meta.get("feed_id"):
        print(f"{a.dia}: já publicado ({meta['feed_id']})"); return
    if post.get("suspenso"):
        print(f"{a.dia}: post suspenso no post.json"); log(a.dia, "-", "", "suspenso"); return
    hh, mm = map(int, post.get("hora", "18:00").split(":"))
    alvo = dt.datetime.now(BRT).replace(hour=hh, minute=mm, second=0, microsecond=0) - dt.timedelta(minutes=15)
    if not a.agora and dt.datetime.now(BRT) < alvo:
        print(f"{a.dia}: ainda não é a hora ({post.get('hora')})"); return
    erro = ""
    for tentativa in range(1, 4):
        try:
            publicar(a.dia, pasta, meta); erro = ""; break
        except Exception as e:
            erro = str(e); log(a.dia, "-", "", f"tentativa_{tentativa}", erro)
            if tentativa < 3:
                time.sleep(300)
    meta_p.write_text(json.dumps(meta, ensure_ascii=False, indent=2))
    if erro:
        sys.exit(f"falhou após 3 tentativas: {erro}")


if __name__ == "__main__":
    main()
