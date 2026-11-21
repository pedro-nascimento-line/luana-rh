# Luana Buzolin · Instagram @luanabuzolin.rh

Operação 100% autônoma dos carrosséis e posts do perfil de RH da Luana Buzolin: pesquisa, texto, arte e publicação,
sem aprovação humana. Reels ficam com a agência e não passam por aqui. Mesma arquitetura do projeto Acta Dei.

## Como funciona

| Quando | Quem | O quê |
| --- | --- | --- |
| Domingo | Tarefa agendada do Cowork (Sonnet) | Mantém o cronograma (Claude Sheet) com 4 semanas à frente (`scripts/PROMPT_CRONOGRAMA.md`) |
| Domingo | Tarefa agendada do Cowork (Opus) | Pesquisa e grava os `post.json` da semana em `posts/AAAA-MM-DD/` (`scripts/PROMPT_PACOTE_SEMANAL.md`) |
| Logo após o commit | GitHub Actions `build.yml` | Busca a foto da capa no Unsplash (`scripts/foto.py`, com filtro de texto) e gera os cards JPEG 1080×1350 (`scripts/render.py`) |
| Seg, ter, qui 17:52 e sex 11:52 | Tarefas agendadas do Cowork (Haiku) | Gravam `gatilho/publicar.txt`, o que dispara a publicação |
| Na hora do post | GitHub Actions `publish.yml` | Publica pela API do Instagram (`scripts/publish.py`); crons de reserva às 18:06, 12:06 e 19:36 |
| Toda segunda | GitHub Actions `refresh-token.yml` | Renova o token do Instagram |

As imagens ficam públicas pelo GitHub Pages (a Meta baixa o JPEG na hora de publicar).

## Secrets e variáveis (Settings › Secrets and variables › Actions)

| Nome | Tipo | Para quê |
| --- | --- | --- |
| `IG_ACCESS_TOKEN` | Secret | Token do Instagram da Luana (Instagram API with Instagram Login, app Followup) |
| `IG_USER_ID` | Secret | ID numérico da conta profissional da Luana |
| `ACTIONS_PAT` | Secret | Token do GitHub com permissão de escrever secrets neste repositório (renovação do token) |
| `UNSPLASH_ACCESS_KEY` | Secret | Chave de acesso da API do Unsplash (fotos das capas) |
| `PAGES_BASE` | Variável | `https://pedro-nascimento-line.github.io/luana-rh` |

## Padrão visual

Manual de marca Luana Buzolin (out/2026). Empresas: Azul Noite `#14263F` com texto Linho `#F5F0E6`. Profissionais:
Linho com texto Verde Raiz `#264A3D`. Areia `#D9C7A8` só em linhas e grafismos. Petróleo `#1F5560` em destaques.
Títulos em serifa (Iowan Old Style; Source Serif 4 no render), texto em Cera Pro (Outfit no render).

## Parar ou corrigir um post

- Suspender: no `post.json` do dia, acrescente `"suspenso": true`. O `publish.py` pula o dia.
- Regenerar as artes: Actions › Gerar artes do post › Run workflow › informe a data.
- Publicar manualmente um dia: Actions › Publicar no Instagram › Run workflow › informe a data.
- Banco de fotos de reserva: coloque JPEGs em `banco/empresas/` ou `banco/profissionais/` com o tema no nome do arquivo.
