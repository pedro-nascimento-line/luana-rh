#!/usr/bin/env python3
"""Gera os cards (JPEG 1080x1350) de um post a partir do post.json.

Uso: python3 scripts/render.py posts/AAAA-MM-DD

Padrão visual aprovado (manual de marca Luana Buzolin, nov/2026):
- Empresas: fundo Azul Noite #14263F, texto Linho #F5F0E6.
- Profissionais: fundo Linho #F5F0E6, texto Verde Raiz #264A3D.
- Areia #D9C7A8 só em linhas e grafismos, nunca em texto. Petróleo #1F5560 para destaques.
- Títulos em serifa (Iowan Old Style; alternativa Source Serif 4), texto em Cera Pro (alternativa Outfit).
- Sem rótulo de público no topo, só a numeração. Rodapé: LUANA BUZOLIN + @luanabuzolin.rh.
- Uma palavra do título em itálico: no post.json, marque com *asteriscos*.

Tipos de tela aceitos em post.json["telas"] (ver scripts/MODELO_POST.json):
  capa, comparativo, antes_depois, linha_tempo, numero, esquema, riscados, fechamento, mito_verdade
"""
import html, json, os, re, sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
FONTDIR = Path(os.environ.get("FONTDIR", RAIZ / "node_modules/@fontsource"))
SERIF = "'Iowan Old Style', 'Iowan Old Style BT', 'Source Serif 4', Georgia, serif"
SANS = "'Cera Pro', 'Outfit', sans-serif"
AREIA = "#D9C7A8"
TEMAS = {
    "empresas":      {"bg": "#14263F", "fg": "#F5F0E6", "rgb": "245,240,230", "linha": "2px solid #D9C7A8", "forte": "#F5F0E6", "forte_fg": "#14263F"},
    "profissionais": {"bg": "#F5F0E6", "fg": "#264A3D", "rgb": "38,74,61",   "linha": "3px solid #D9C7A8", "forte": "#264A3D", "forte_fg": "#F5F0E6"},
}
TEMAS["candidatos"] = TEMAS["profissionais"]


def esc(s):
    """Escapa HTML e converte *palavra* em itálico."""
    s = html.escape(str(s or ""), quote=False)
    return re.sub(r"\*(.+?)\*", r'<em style="font-style: italic">\1</em>', s)


class Card:
    def __init__(self, publico):
        self.p = "empresas" if publico == "empresas" else "profissionais"
        self.T = TEMAS[self.p]

    def mut(self, a):
        return f"rgba({self.T['rgb']},{a})"

    # ---------- blocos comuns
    def topo(self, n, total):
        return (f'<div style="display:flex;justify-content:flex-end;padding-bottom:28px;border-bottom:{self.T["linha"]};'
                f'font-size:22px;font-weight:500;letter-spacing:.28em"><span>{n:02d} / {total:02d}</span></div>')

    def rodape(self, capa=False):
        d = ('<span style="font-size:22px;font-weight:500;letter-spacing:.2em;text-transform:uppercase">Arraste →</span>' if capa
             else '<span style="font-size:22px;font-weight:400;letter-spacing:.06em">@luanabuzolin.rh</span>')
        return (f'<div style="display:flex;justify-content:space-between;align-items:center">'
                f'<span style="font-family:{SERIF};font-size:26px;letter-spacing:.14em">LUANA BUZOLIN</span>{d}</div>')

    def titulo(self, num, txt):
        return (f'<div style="display:flex;align-items:baseline;gap:28px">'
                f'<span style="font-family:{SERIF};font-style:italic;font-size:72px;line-height:1">{esc(num)}</span>'
                f'<h2 style="margin:0;font-family:{SERIF};font-weight:400;font-size:60px;line-height:1.12">{esc(txt)}</h2></div>')

    def par(self, txt, size=32):
        if not txt:
            return ""
        return f'<p style="margin:0;font-size:{size}px;font-weight:300;line-height:1.45;color:{self.mut(.88)}">{esc(txt)}</p>'

    def acao(self, txt):
        if not txt:
            return ""
        rot = "O que fazer" if self.p == "empresas" else "Faça assim"
        return (f'<div style="display:flex;flex-direction:column;gap:14px;padding-top:28px;border-top:{self.T["linha"]}">'
                f'<span style="font-size:20px;font-weight:600;letter-spacing:.28em;text-transform:uppercase">{rot}</span>'
                f'<p style="margin:0;font-size:30px;font-weight:400;line-height:1.45">{esc(txt)}</p></div>')

    def nota(self, txt):
        if not txt:
            return ""
        return f'<p style="margin:0;font-size:22px;font-weight:400;line-height:1.5;color:{self.mut(.8)}">{esc(txt)}</p>'

    def rot(self, txt, forte=False):
        cor = "inherit" if forte else self.mut(.75)
        return f'<span style="font-size:20px;font-weight:600;letter-spacing:.2em;text-transform:uppercase;color:{cor}">{esc(txt)}</span>'

    def pagina(self, n, total, miolo, capa=False, gap=36):
        T = self.T
        return (f'<div style="width:1080px;height:1350px;box-sizing:border-box;padding:88px 96px;background:{T["bg"]};color:{T["fg"]};'
                f'font-family:{SANS};display:flex;flex-direction:column;justify-content:space-between">'
                f'{self.topo(n, total)}<div style="display:flex;flex-direction:column;gap:{gap}px">{miolo}</div>{self.rodape(capa)}</div>')

    def check(self, s=28, cor=AREIA, w=2.5):
        return (f'<svg width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="{cor}" stroke-width="{w}" stroke-linecap="round" '
                f'stroke-linejoin="round" aria-hidden="true"><path d="M5 12l5 5L20 7"></path></svg>')

    def seta(self, d="d", s=40):
        cor = AREIA if self.p == "empresas" else self.T["fg"]
        p = {"d": "M12 4v16M6 14l6 6 6-6", "r": "M4 12h16M14 6l6 6-6 6"}[d]
        return (f'<svg width="{s}" height="{s}" viewBox="0 0 24 24" fill="none" stroke="{cor}" stroke-width="2" stroke-linecap="round" '
                f'stroke-linejoin="round" aria-hidden="true"><path d="{p}"></path></svg>')

    def caixa_forte(self, inner, pad="28px 32px", gap=12):
        if self.p == "empresas":
            return f'<div style="display:flex;flex-direction:column;gap:{gap}px;padding:{pad};border:2px solid {AREIA};border-radius:8px">{inner}</div>'
        return f'<div style="display:flex;flex-direction:column;gap:{gap}px;padding:{pad};background:#264A3D;color:#F5F0E6;border-radius:8px">{inner}</div>'

    def caixa_leve(self, inner, pad="28px 32px", gap=12):
        return f'<div style="display:flex;flex-direction:column;gap:{gap}px;padding:{pad};border:2px solid {self.mut(.3)};border-radius:8px">{inner}</div>'

    # ---------- tipos de tela
    def capa(self, s, n, total, foto_src):
        if foto_src and self.p == "empresas":
            img = (f'<div style="position:relative;height:440px;border-radius:8px;overflow:hidden;background:#14263F">'
                   f'<img src="{foto_src}" style="width:100%;height:100%;object-fit:cover;object-position:{s.get("posicao","center")};display:block;'
                   f'filter:grayscale(100%) contrast(1.08);opacity:.62;mix-blend-mode:luminosity">'
                   f'<div style="position:absolute;inset:0;background:linear-gradient(180deg,rgba(20,38,63,0) 55%,rgba(20,38,63,.55) 100%)"></div></div>')
        elif foto_src:
            img = (f'<div style="height:440px;border-radius:8px;overflow:hidden;background:{AREIA}"><img src="{foto_src}" '
                   f'style="width:100%;height:100%;object-fit:cover;object-position:{s.get("posicao","center")};display:block;filter:saturate(.85) sepia(.12)"></div>')
        else:  # sem foto: grafismo tipográfico em Areia
            img = (f'<div style="height:440px;border-radius:8px;border:2px solid {AREIA};display:flex;align-items:center;justify-content:center">'
                   f'<span style="font-family:{SERIF};font-style:italic;font-size:220px;line-height:1;color:{self.mut(.18)}">“</span></div>')
        tam = s.get("tamanho") or (78 if len(s.get("titulo", "")) > 60 else 88)
        m = (img + f'<h1 style="margin:0;font-family:{SERIF};font-weight:400;font-size:{tam}px;line-height:1.08;letter-spacing:-.01em">{esc(s["titulo"])}</h1>'
             f'<div style="width:112px;height:4px;background:{AREIA}"></div>'
             f'<p style="margin:0;font-size:38px;font-weight:300;line-height:1.4;color:{self.mut(.88)};max-width:820px">{esc(s.get("subtitulo"))}</p>')
        return self.pagina(n, total, m, capa=True, gap=40)

    def comparativo(self, s, n, total):
        def col(c, forte):
            itens = "".join(
                f'<div style="display:flex;align-items:flex-start;gap:12px"><div style="width:10px;height:10px;margin-top:14px;border-radius:50%;'
                f'background:{AREIA};flex-shrink:0"></div><span style="font-size:28px;font-weight:400;line-height:1.35">{esc(i)}</span></div>'
                for i in c.get("itens", []))
            sub = (f'<span style="font-size:20px;font-weight:600;letter-spacing:.2em;text-transform:uppercase;opacity:.8">{esc(c.get("sub"))}</span>'
                   if c.get("sub") else "")
            inner = (f'<div style="display:flex;flex-direction:column;gap:6px"><span style="font-family:{SERIF};font-size:40px;line-height:1.1">{esc(c["rotulo"])}</span>{sub}</div>'
                     f'<div style="height:2px;background:{AREIA}"></div>{itens}')
            return self.caixa_forte(inner, pad="32px", gap=22) if forte else self.caixa_leve(inner, pad="32px", gap=22)
        m = (self.titulo(s["num"], s["titulo"]) +
             f'<div style="display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:28px">{col(s["a"], False)}{col(s["b"], True)}</div>' +
             self.par(s.get("texto")) + self.acao(s.get("acao")) + self.nota(s.get("nota")))
        return self.pagina(n, total, m)

    def antes_depois(self, s, n, total):
        a, d = s["antes"], s["depois"]
        c1 = self.caixa_leve(self.rot(a.get("rotulo", "Antes")) + f'<span style="font-size:32px;font-weight:300;line-height:1.4;color:{self.mut(.8)}">{esc(a["texto"])}</span>')
        c2 = self.caixa_forte(f'<span style="font-size:20px;font-weight:600;letter-spacing:.2em;text-transform:uppercase">{esc(d.get("rotulo","Depois"))}</span>'
                              f'<span style="font-size:32px;font-weight:400;line-height:1.4">{esc(d["texto"])}</span>')
        m = (self.titulo(s["num"], s["titulo"]) +
             f'<div style="display:flex;flex-direction:column;gap:16px">{c1}<div style="display:flex;justify-content:center">{self.seta("d")}</div>{c2}</div>' +
             self.par(s.get("texto")) + self.acao(s.get("acao")) + self.nota(s.get("nota")))
        return self.pagina(n, total, m)

    def linha_tempo(self, s, n, total):
        passos = s["passos"]
        def passo(p, ult):
            if ult:
                bola = (f'<div style="width:44px;height:44px;border-radius:50%;background:{AREIA};display:flex;align-items:center;justify-content:center;flex-shrink:0">'
                        f'{self.check(24, self.T["bg"], 3)}</div>')
            else:
                bola = f'<div style="width:44px;height:44px;box-sizing:border-box;border-radius:50%;border:3px solid {AREIA};background:{self.T["bg"]};flex-shrink:0"></div>'
            return (f'<div style="position:relative;display:flex;align-items:flex-start;gap:28px">{bola}<div style="display:flex;flex-direction:column;gap:6px">'
                    f'<span style="font-size:20px;font-weight:600;letter-spacing:.2em;text-transform:uppercase;color:{self.mut(.8)}">{esc(p["quando"])}</span>'
                    f'<span style="font-family:{SERIF};font-size:38px;line-height:1.2">{esc(p["texto"])}</span></div></div>')
        tl = (f'<div style="position:relative;display:flex;flex-direction:column;gap:40px;padding:8px 0">'
              f'<div style="position:absolute;left:21px;top:30px;bottom:30px;width:3px;background:{AREIA}"></div>'
              + "".join(passo(p, i == len(passos) - 1) for i, p in enumerate(passos)) + '</div>')
        m = self.titulo(s["num"], s["titulo"]) + tl + self.par(s.get("texto")) + self.acao(s.get("acao")) + self.nota(s.get("nota"))
        return self.pagina(n, total, m)

    def numero(self, s, n, total):
        icones = ""
        if s.get("icones"):
            tot, ch = s["icones"]["total"], s["icones"]["cheios"]
            def pessoa(cheia):
                cor = self.T["fg"] if cheia else "none"
                tr = self.T["fg"] if cheia else self.mut(.45)
                return (f'<svg width="64" height="104" viewBox="0 0 32 52" aria-hidden="true"><circle cx="16" cy="9" r="7.5" fill="{cor}" stroke="{tr}" stroke-width="2"></circle>'
                        f'<path d="M3 50 V30 a13 13 0 0 1 26 0 V50 Z" fill="{cor}" stroke="{tr}" stroke-width="2" stroke-linejoin="round"></path></svg>')
            icones = f'<div style="display:flex;justify-content:space-between">{"".join(pessoa(i < ch) for i in range(tot))}</div>'
        bloco = (f'<div style="display:flex;flex-direction:column;gap:28px;padding:40px 36px;border:2px solid {self.mut(.3)};border-radius:8px">'
                 f'<div style="display:flex;align-items:baseline;gap:20px;flex-wrap:wrap"><span style="font-family:{SERIF};font-size:120px;line-height:.9">{esc(s["destaque"])}</span>'
                 f'<span style="font-family:{SERIF};font-style:italic;font-size:48px">{esc(s.get("complemento"))}</span></div>{icones}'
                 f'<div style="height:3px;background:{AREIA}"></div>'
                 f'<span style="font-size:22px;font-weight:400;color:{self.mut(.85)}">{esc(s.get("legenda"))}</span></div>')
        m = self.titulo(s["num"], s["titulo"]) + bloco + self.par(s.get("texto")) + self.acao(s.get("acao")) + self.nota(s.get("nota"))
        return self.pagina(n, total, m)

    def esquema(self, s, n, total):
        nos = s["nos"]
        def no(txt, ult):
            est = (f"background:{self.T['forte']};color:{self.T['forte_fg']};border:2px solid {self.T['forte']}" if ult
                   else f"border:2px solid {self.mut(.4)}")
            return f'<div style="flex:1;padding:26px 18px;{est};border-radius:10px;text-align:center;font-size:28px;font-weight:500;line-height:1.25">{esc(txt)}</div>'
        seta = f'<div style="flex-shrink:0">{self.seta("r", 44)}</div>'
        fila = seta.join(no(t, i == len(nos) - 1) for i, t in enumerate(nos))
        destaque = ""
        if s.get("destaque"):
            destaque = (f'<div style="display:flex;align-items:center;gap:14px;padding:18px 22px;border:2px solid {AREIA};border-radius:8px">'
                        f'{self.check(30)}<span style="font-size:26px;font-weight:500">{esc(s["destaque"])}</span></div>')
        bloco = (f'<div style="display:flex;flex-direction:column;gap:22px;padding:36px 32px;border:2px solid {self.mut(.3)};border-radius:8px">'
                 f'<div style="display:flex;align-items:center;gap:14px">{fila}</div>{destaque}</div>')
        m = self.titulo(s["num"], s["titulo"]) + bloco + self.par(s.get("texto")) + self.acao(s.get("acao")) + self.nota(s.get("nota"))
        return self.pagina(n, total, m)

    def riscados(self, s, n, total):
        x = "".join(f'<span style="padding:16px 22px;border:2px solid {self.mut(.25)};border-radius:14px;font-size:26px;font-weight:300;'
                    f'color:{self.mut(.65)};text-decoration:line-through">{esc(i)}</span>' for i in s["evitar"])
        ok = "".join(f'<span style="padding:16px 22px;border:2px solid {AREIA};border-radius:14px;font-size:26px;font-weight:400">{esc(i)}</span>' for i in s["usar"])
        bloco = (f'<div style="display:grid;grid-template-columns:minmax(0,1fr) 56px minmax(0,1fr);align-items:center;gap:16px">'
                 f'<div style="display:flex;flex-direction:column;gap:14px">{self.rot(s.get("rotulo_evitar","Evite"))}{x}</div>'
                 f'<div style="display:flex;justify-content:center">{self.seta("r", 48)}</div>'
                 f'<div style="display:flex;flex-direction:column;gap:14px">{self.rot(s.get("rotulo_usar","Use"), True)}{ok}</div></div>')
        m = self.titulo(s["num"], s["titulo"]) + bloco + self.par(s.get("texto")) + self.acao(s.get("acao")) + self.nota(s.get("nota"))
        return self.pagina(n, total, m)

    def fechamento(self, s, n, total):
        cta2 = (f'<p style="margin:0;font-size:30px;font-weight:300;line-height:1.45;opacity:.88">{esc(s["cta2"])}</p>' if s.get("cta2") else "")
        m = (f'<h2 style="margin:0;font-family:{SERIF};font-weight:400;font-size:84px;line-height:1.1">{esc(s["titulo"])}</h2>'
             f'<div style="width:112px;height:4px;background:{AREIA}"></div>{self.par(s.get("texto"), 36)}'
             + self.caixa_forte(f'<p style="margin:0;font-size:32px;font-weight:500;line-height:1.4">{esc(s["cta"])}</p>{cta2}', pad="40px 44px", gap=20)
             + f'<p style="margin:0;font-size:20px;font-weight:300;line-height:1.5;color:{self.mut(.8)}">Fontes: {esc(s["fontes"])}</p>')
        return self.pagina(n, total, m, gap=40)

    def mito_verdade(self, s, n, total):
        """Post único. veredito: 'Mito' ou 'Verdade'. barra opcional: {'partes': [45, 45], 'rotulo': '...'}"""
        T = self.T
        barra = ""
        if s.get("barra"):
            b = s["barra"]
            partes = "".join(
                f'<div style="flex:{v};display:flex;align-items:center;justify-content:center;height:64px;'
                f'{"background:" + AREIA + ";color:" + T["bg"] if i == 0 else "border:2px solid " + AREIA}; font-size:26px;font-weight:600">{v} dias</div>'
                for i, v in enumerate(b["partes"]))
            barra = (f'<div style="display:flex;flex-direction:column;gap:14px"><div style="display:flex;gap:8px">{partes}</div>'
                     f'<span style="font-size:22px;font-weight:400;color:{self.mut(.85)}">{esc(b.get("rotulo"))}</span></div>')
        m = (f'<span style="font-size:22px;font-weight:600;letter-spacing:.28em;text-transform:uppercase">Mito ou verdade?</span>'
             f'<p style="margin:0;font-family:{SERIF};font-size:64px;line-height:1.15">“{esc(s["afirmacao"])}”</p>'
             f'<div style="display:flex;align-items:center;gap:28px"><div style="height:4px;width:112px;background:{AREIA}"></div>'
             f'<span style="font-family:{SERIF};font-style:italic;font-size:150px;line-height:1">{esc(s["veredito"])}.</span></div>'
             + barra + self.par(s.get("explicacao")) +
             f'<p style="margin:0;font-size:22px;font-weight:400;line-height:1.5;color:{self.mut(.8)}">Base: {esc(s["base"])}</p>'
             + (f'<p style="margin:0;font-size:30px;font-weight:500;line-height:1.4">{esc(s["cta"])}</p>' if s.get("cta") else ""))
        return (f'<div style="width:1080px;height:1350px;box-sizing:border-box;padding:88px 96px;background:{T["bg"]};color:{T["fg"]};'
                f'font-family:{SANS};display:flex;flex-direction:column;justify-content:space-between">'
                f'<div style="padding-bottom:28px;border-bottom:{T["linha"]}"></div>'
                f'<div style="display:flex;flex-direction:column;gap:36px">{m}</div>{self.rodape()}</div>')


def font_face():
    fs = [("Outfit", "outfit", "normal", w, f"outfit-latin-{w}-normal.woff2") for w in (300, 400, 500, 600)]
    fs += [("Source Serif 4", "source-serif-4", st, 400, f"source-serif-4-latin-400-{st}.woff2") for st in ("normal", "italic")]
    return "".join(f"@font-face{{font-family:'{f}';font-style:{st};font-weight:{w};src:url('file://{FONTDIR}/{pkg}/files/{fn}') format('woff2');}}"
                   for f, pkg, st, w, fn in fs)


def montar(post, pasta):
    c = Card(post["publico"].lower())
    telas = post["telas"]
    total = len(telas)
    capa = pasta / "capa.jpg"
    foto_src = "file://" + str(capa.resolve()) if capa.exists() else None
    out = []
    for i, s in enumerate(telas, 1):
        tipo = s["tipo"]
        if tipo == "capa":
            out.append(c.capa(s, i, total, foto_src))
        else:
            out.append(getattr(c, tipo)(s, i, total))
    return out


def main():
    pasta = Path(sys.argv[1])
    post = json.loads((pasta / "post.json").read_text())
    if post.get("artes_prontas"):
        print(f"{pasta}: artes prontas, nada a gerar"); return
    paginas = montar(post, pasta)
    from playwright.sync_api import sync_playwright
    for old in pasta.glob("card_*.jpg"):
        old.unlink()
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1080, "height": 1350})
        for i, corpo in enumerate(paginas, 1):
            doc = f'<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><style>{font_face()}body{{margin:0}}</style></head><body>{corpo}</body></html>'
            tmp = pasta / f"_card_{i:02d}.html"
            tmp.write_text(doc)
            pg.goto("file://" + str(tmp.resolve()))
            pg.evaluate("document.fonts.ready")
            pg.wait_for_timeout(200)
            pg.screenshot(path=str(pasta / f"card_{i:02d}.jpg"), type="jpeg", quality=92, clip={"x": 0, "y": 0, "width": 1080, "height": 1350})
            tmp.unlink()
        b.close()
    # legenda e hashtags em arquivos separados (o publish.py lê daqui)
    (pasta / "legenda.txt").write_text(post["legenda"].strip() + "\n")
    (pasta / "hashtags.txt").write_text(post.get("hashtags", "").strip() + "\n")
    print(f"{pasta}: {len(paginas)} cards")


if __name__ == "__main__":
    main()
