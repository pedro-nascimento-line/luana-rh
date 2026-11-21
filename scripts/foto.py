#!/usr/bin/env python3
"""Busca a foto da capa de um post e salva em posts/<dia>/capa.jpg.

Uso: python3 scripts/foto.py posts/AAAA-MM-DD

Ordem de tentativa:
1. Já existe capa.jpg na pasta: mantém.
2. Unsplash (precisa do secret UNSPLASH_ACCESS_KEY): busca por post.json["foto"]["busca"], descarta
   fotos com texto legível (OCR com RapidOCR, e palavras como sign/text/resume na descrição) e fotos já usadas em outros posts; registra o crédito.
3. Banco local banco/<publico>/: escolhe o arquivo cujo nome tem mais palavras em comum com o tema.
Se nada der certo, a capa sai sem foto (grafismo tipográfico) e o post é publicado assim mesmo.
"""
import io, json, os, re, sys, unicodedata
from pathlib import Path
import requests
from PIL import Image

RAIZ = Path(__file__).resolve().parent.parent
KEY = os.environ.get("UNSPLASH_ACCESS_KEY", "").strip()
UA = {"Accept-Version": "v1", "Authorization": f"Client-ID {KEY}"}


def norm(s):
    s = unicodedata.normalize("NFKD", s.lower())
    return "".join(c for c in s if not unicodedata.combining(c))


PROIBIDAS = ("text", "sign", "letter", "word", "resume", "cv ", "document", "poster", "typography", "neon", "logo",
            "brand", "quote", "book", "newspaper", "screen", "laptop screen", "billboard", "label")
_OCR = None


def tem_texto(img):
    """True se o OCR (RapidOCR) achar texto legível na foto. Sem OCR instalado, não bloqueia."""
    global _OCR
    try:
        import numpy as np
        from rapidocr_onnxruntime import RapidOCR
    except ImportError:
        return False
    if _OCR is None:
        _OCR = RapidOCR()
    g = img.convert("RGB")
    g.thumbnail((1280, 1280))
    res, _ = _OCR(np.array(g))
    return any(float(c) >= 0.6 and len(t.strip()) >= 3 for _, t, c in (res or []))


def metadados_suspeitos(foto):
    txt = " ".join(filter(None, [foto.get("description"), foto.get("alt_description")] +
                          [t.get("title", "") for t in foto.get("tags", [])])).lower()
    return any(p in txt for p in PROIBIDAS)


def usadas():
    ids = set()
    for p in (RAIZ / "posts").glob("*/post.json"):
        try:
            f = (json.loads(p.read_text()).get("foto") or {}).get("escolhida") or {}
            if f.get("id"):
                ids.add(f["id"])
        except Exception:
            pass
    return ids


def salvar(img, destino):
    img = img.convert("RGB")
    img.thumbnail((1800, 1800))
    img.save(destino, quality=88)


def unsplash(post, pasta):
    busca = (post.get("foto") or {}).get("busca")
    if not (KEY and busca):
        return False
    ja = usadas()
    r = requests.get("https://api.unsplash.com/search/photos", headers=UA, timeout=30,
                     params={"query": busca, "orientation": "landscape", "content_filter": "high", "per_page": 15})
    r.raise_for_status()
    for foto in r.json().get("results", []):
        if foto["id"] in ja or metadados_suspeitos(foto):
            continue
        prev = requests.get(foto["urls"]["regular"], timeout=60)
        img = Image.open(io.BytesIO(prev.content))
        if tem_texto(img):
            print(f"  descartada {foto['id']}: tem texto")
            continue
        full = requests.get(foto["urls"]["raw"], params={"w": 1800, "fm": "jpg", "q": 85}, timeout=60)
        salvar(Image.open(io.BytesIO(full.content)), pasta / "capa.jpg")
        # exigência da API do Unsplash: registrar o download
        requests.get(foto["links"]["download_location"], headers=UA, timeout=30)
        autor = foto["user"]["name"]
        post["foto"]["escolhida"] = {"fonte": "unsplash", "id": foto["id"], "autor": autor,
                                     "link": foto["links"]["html"]}
        (pasta / "credito.txt").write_text(f"Foto da capa: {autor} / Unsplash\n")
        print(f"  capa: Unsplash {foto['id']} ({autor})")
        return True
    return False


def banco(post, pasta):
    pub = post["publico"]
    tema = set(re.findall(r"[a-z]{4,}", norm(post.get("tema", "") + " " + (post.get("foto") or {}).get("busca", ""))))
    melhores = []
    for f in (RAIZ / "banco" / pub).glob("*.jp*g"):
        palavras = set(re.findall(r"[a-z]{4,}", norm(f.stem)))
        melhores.append((len(tema & palavras), f))
    melhores.sort(key=lambda x: -x[0])
    if not melhores or melhores[0][0] == 0:
        return False
    f = melhores[0][1]
    salvar(Image.open(f), pasta / "capa.jpg")
    post.setdefault("foto", {})["escolhida"] = {"fonte": "banco", "arquivo": f.name}
    print(f"  capa: banco {f.name}")
    return True


def main():
    pasta = Path(sys.argv[1])
    pj = pasta / "post.json"
    post = json.loads(pj.read_text())
    if post.get("artes_prontas") or not post.get("foto") or (pasta / "capa.jpg").exists():
        print(f"{pasta}: capa não precisa ser buscada"); return
    ok = False
    try:
        ok = unsplash(post, pasta)
    except Exception as e:
        print(f"  Unsplash falhou: {e}")
    if not ok:
        ok = banco(post, pasta)
    if ok:
        pj.write_text(json.dumps(post, ensure_ascii=False, indent=2))
    else:
        print("  sem foto: a capa sai com grafismo")


if __name__ == "__main__":
    main()
