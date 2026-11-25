"""Baixa para data/raw/ os dados brutos com download direto e confere o SHA-256.

Automáticos: PRODES Caatinga (WFS do TerraBrasilis), focos do INPE (satélite
de referência, 2014–2024) e OSM (Geofabrik, jan/2020). MapBiomas e CHIRPS são
exportados à mão no Google Earth Engine (src/data/gee_*.js); aqui só são
conferidos.

Os hashes esperados vêm de docs/fontes-de-dados.md (fonte única). Regras:
- arquivo que já existe nunca é sobrescrito, só conferido;
- arquivo novo é baixado como .part e só ganha o nome final se o hash bater;
- nenhum outro script grava em data/raw/.

O zip do PRODES é montado na hora pelo GeoServer e grava a data do download
no cabeçalho do .dbf, então o hash do arquivo muda a cada download. Ele é
conferido pelo hash do conteúdo, que ignora essa data.

Uso (na raiz do repositório):
    python src/data/download.py              # baixa o que falta e confere tudo
    python src/data/download.py --verificar  # só confere, não baixa nada
    python src/data/download.py --raw PASTA  # outro destino (ex.: teste de sala limpa)
"""

import argparse
import hashlib
import re
import shutil
import ssl
import sys
import urllib.error
import urllib.request
import zipfile
from collections import namedtuple
from pathlib import Path

import certifi

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs" / "fontes-de-dados.md"

Fonte = namedtuple("Fonte", "url acesso manual")

WFS = ("https://terrabrasilis.dpi.inpe.br/geoserver/prodes-caatinga-nb/ows?service=WFS&version=1.0.0"
       "&request=GetFeature&typeName=prodes-caatinga-nb:{}&bbox=-40.97,-10.0,-39.84,-8.61&outputFormat=SHAPE-ZIP")
FOCOS = "https://dataserver-coids.inpe.br/queimadas/queimadas/focos/csv/anual/Brasil_sat_ref/{}"
GEOFABRIK = "https://download.geofabrik.de/south-america/brazil/nordeste/{}"

# (pasta em data/raw, arquivo): Fonte(url ou None, data de acesso, script manual)
FONTES = {
    ("prodes", "yearly_deforestation.zip"):
        Fonte(WFS.format("yearly_deforestation"), "23/11/2026", None),
    ("prodes", "accumulated_deforestation_2000.zip"):
        Fonte(WFS.format("accumulated_deforestation_2000"), "23/11/2026", None),
    **{("queimadas", f"focos_br_ref_{a}.zip"): Fonte(FOCOS.format(f"focos_br_ref_{a}.zip"), "23/11/2026", None)
       for a in range(2014, 2025)},
    ("osm", "nordeste-200101.osm.pbf"):
        Fonte(GEOFABRIK.format("nordeste-200101.osm.pbf"), "24/11/2026", None),
    ("mapbiomas", "mapbiomas_c10_petrolina_juazeiro_2015_2024.tif"):
        Fonte(None, "23/11/2026", "src/data/gee_mapbiomas.js"),
    ("chirps", "chirps_petrolina_juazeiro_t2017_2025.tif"):
        Fonte(None, "24/11/2026", "src/data/gee_chirps.js"),
}


def ler_hashes(doc: Path) -> dict:
    """{(pasta, arquivo): [sha do arquivo, sha do conteúdo (opcional)]} das tabelas do doc."""
    hashes, pasta = {}, None
    for linha in doc.read_text(encoding="utf-8").splitlines():
        if m := re.match(r"\| Arquivo \(`data/raw/([^`]+)/`\)", linha):
            pasta = m.group(1)
        elif pasta and (m := re.match(r"\| `([^`]+)` \|", linha)):
            hashes[(pasta, m.group(1))] = re.findall(r"`([0-9a-f]{64})`", linha)
        elif not linha.startswith("|"):
            pasta = None
    return hashes


def sha256_arquivo(caminho: Path) -> str:
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def sha256_conteudo_zip(caminho: Path) -> str:
    """Hash dos arquivos dentro do zip, com a data do cabeçalho do .dbf (bytes 1–3) zerada."""
    h = hashlib.sha256()
    with zipfile.ZipFile(caminho) as z:
        for nome in sorted(z.namelist()):
            dados = z.read(nome)
            if nome.lower().endswith(".dbf"):
                dados = dados[:1] + b"\0\0\0" + dados[4:]
            h.update(nome.encode() + dados)
    return h.hexdigest()


def confere(caminho: Path, esperados: list) -> bool:
    if sha256_arquivo(caminho) == esperados[0]:
        return True
    return len(esperados) > 1 and sha256_conteudo_zip(caminho) == esperados[1]


def baixar(url: str, destino: Path):
    """Baixa com verificação TLS pelas raízes do certifi (Mozilla), não pelas do sistema:
    o repositório de raízes do Windows pode estar desatualizado e recusar certificados válidos."""
    req = urllib.request.Request(url, headers={"User-Agent": "projeto-ml-ods/download.py"})
    ctx = ssl.create_default_context(cafile=certifi.where())
    with urllib.request.urlopen(req, timeout=600, context=ctx) as resp, open(destino, "wb") as f:
        shutil.copyfileobj(resp, f, 1 << 20)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--verificar", action="store_true", help="só confere, não baixa")
    parser.add_argument("--raw", type=Path, default=ROOT / "data" / "raw", help="pasta de destino")
    args = parser.parse_args()

    hashes = ler_hashes(DOC)
    if set(hashes) != set(FONTES):
        sys.exit(f"download.py e {DOC.name} divergem: "
                 f"sem hash no doc {sorted(set(FONTES) - set(hashes))}; "
                 f"sem fonte no script {sorted(set(hashes) - set(FONTES))}")

    problemas = 0
    for (pasta, arquivo), fonte in FONTES.items():
        caminho = args.raw / pasta / arquivo
        rotulo = f"{pasta}/{arquivo}"
        if caminho.exists():
            ok = confere(caminho, hashes[(pasta, arquivo)])
            print(f"{'OK      ' if ok else 'DIVERGE '} {rotulo}" + ("" if ok else "  (hash diferente; arquivo não alterado)"))
        elif fonte.manual:
            ok = False
            print(f"MANUAL   {rotulo}  -> rodar {fonte.manual} no Google Earth Engine e copiar para {pasta}/")
        elif args.verificar:
            ok = False
            print(f"FALTA    {rotulo}")
        else:
            caminho.parent.mkdir(parents=True, exist_ok=True)
            parcial = caminho.with_name(caminho.name + ".part")
            print(f"baixando {rotulo} ...", end=" ", flush=True)
            try:
                baixar(fonte.url, parcial)
            except (urllib.error.URLError, OSError) as erro:
                parcial.unlink(missing_ok=True)
                print(f"ERRO de download: {erro}")
                problemas += 1
                continue
            ok = confere(parcial, hashes[(pasta, arquivo)])
            if ok:
                parcial.rename(caminho)
                print(f"OK ({caminho.stat().st_size / 1e6:.1f} MB)")
            else:
                parcial.unlink()
                print("HASH DIFERENTE, descartado (a fonte pode ter sido reprocessada)")
        problemas += not ok

    print(f"\n{len(FONTES) - problemas}/{len(FONTES)} arquivos conferidos em {args.raw}")
    sys.exit(1 if problemas else 0)


if __name__ == "__main__":
    main()
