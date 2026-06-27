# -*- coding: utf-8 -*-
"""
Aplicador da tradução PT-BR (NÃO-OFICIAL) do New Cycle.

Não contém o jogo — só a tradução. Você precisa ter o New Cycle instalado.
Faz backup do original, instala a tradução e ajusta o catálogo (CRC).
Sem dependências: usa apenas a biblioteca padrão do Python.

Uso:
    python aplicar.py            -> aplica a tradução
    python aplicar.py restaurar  -> volta o jogo ao original
    python aplicar.py "C:\\caminho\\do\\New Cycle"   -> caminho manual
"""
import os, sys, shutil, struct

if getattr(sys, "frozen", False):
    AQUI = os.path.dirname(sys.executable)        # ao lado do .exe (PyInstaller)
else:
    AQUI = os.path.dirname(os.path.abspath(__file__))
BUNDLE_NOME = "localization-string-tables-english(en)_assets_all.bundle"
PREFIXO = "localization-string-tables-english(en)_assets_all"
SUB_BUNDLES = os.path.join("New Cycle_Data", "StreamingAssets", "aa", "StandaloneWindows64")
SUB_CATALOG = os.path.join("New Cycle_Data", "StreamingAssets", "aa", "catalog.bin")
PADROES = [
    r"C:\Program Files (x86)\Steam\steamapps\common\New Cycle",
    r"C:\Program Files\Steam\steamapps\common\New Cycle",
    r"D:\SteamLibrary\steamapps\common\New Cycle",
    r"D:\Steam\steamapps\common\New Cycle",
    r"E:\SteamLibrary\steamapps\common\New Cycle",
]


def achar_jogo():
    for p in PADROES:
        if os.path.isfile(os.path.join(p, "New Cycle.exe")):
            return p
    return None


def _crc_offset(catalog: bytes, tam_original: int):
    """Acha o CRC do bundle no catalog.bin: nome -> ponteiro -> CRC a -20, confere pelo tamanho."""
    off = catalog.find(PREFIXO.encode("ascii"))
    if off < 0:
        return None
    ponteiro = struct.pack("<i", off)
    start = 0
    while True:
        p = catalog.find(ponteiro, start)
        if p < 0:
            return None
        c = p - 20
        if c >= 0 and c + 8 <= len(catalog) and struct.unpack_from("<i", catalog, c + 4)[0] == tam_original:
            return c
        start = p + 1


def _escrever(path, data: bytes):
    tmp = path + ".tmp"
    with open(tmp, "wb") as f:
        f.write(data); f.flush(); os.fsync(f.fileno())
    os.replace(tmp, path)


def aplicar(game):
    bundle = os.path.join(game, SUB_BUNDLES, BUNDLE_NOME)
    catalog = os.path.join(game, SUB_CATALOG)
    fonte = os.path.join(AQUI, BUNDLE_NOME)
    if not os.path.isfile(fonte):
        return f"ERRO: não achei a tradução ({BUNDLE_NOME}) junto deste script."
    if not os.path.isfile(bundle):
        return f"ERRO: não achei o jogo em {bundle}\nUse: python aplicar.py \"caminho do New Cycle\""
    if not os.path.isfile(catalog):
        return f"ERRO: catalog.bin não encontrado em {catalog}"

    # 1) backup (uma vez)
    for f in (bundle, catalog):
        if not os.path.exists(f + ".orig.bak"):
            shutil.copy2(f, f + ".orig.bak")
            print("  backup:", os.path.basename(f) + ".orig.bak")
    tam_original = os.path.getsize(bundle + ".orig.bak")

    # 2) instala o bundle traduzido
    _escrever(bundle, open(fonte, "rb").read())
    print("  tradução instalada no bundle")

    # 3) zera o CRC no catálogo (senão o jogo recusa o bundle alterado)
    data = bytearray(open(catalog, "rb").read())
    off = _crc_offset(bytes(data), tam_original)
    if off is None:
        # rollback do bundle pra não deixar o jogo quebrado
        shutil.copy2(bundle + ".orig.bak", bundle)
        return ("ERRO: não localizei o CRC no catálogo — provavelmente a SUA versão do jogo "
                "é diferente da usada nesta tradução. Tradução revertida; nada foi quebrado.")
    if struct.unpack_from("<I", data, off)[0] != 0:
        struct.pack_into("<I", data, off, 0)
        _escrever(catalog, bytes(data))
        print(f"  CRC ajustado no catálogo (offset {off})")
    else:
        print("  CRC já estava ajustado")

    return ("OK! Tradução aplicada com sucesso.\n"
            ">> No jogo: Settings -> Language -> English (o PT-BR foi posto sobre o inglês).")


def restaurar(game):
    bundle = os.path.join(game, SUB_BUNDLES, BUNDLE_NOME)
    catalog = os.path.join(game, SUB_CATALOG)
    faltam = [f for f in (bundle, catalog) if not os.path.exists(f + ".orig.bak")]
    if faltam:
        return "ERRO: backup .orig.bak não encontrado — nada para restaurar."
    for f in (bundle, catalog):
        shutil.copy2(f + ".orig.bak", f)
    return "OK! Jogo restaurado ao original."


def main():
    args = [a for a in sys.argv[1:]]
    modo = "aplicar"
    game = None
    for a in args:
        if a.lower() == "restaurar":
            modo = "restaurar"
        elif os.path.isdir(a):
            game = a
    game = game or achar_jogo()
    print("=== Tradução PT-BR (não-oficial) — New Cycle ===")
    if not game:
        print("Não achei o New Cycle nos caminhos padrão da Steam.")
        print('Rode assim:  python aplicar.py "C:\\caminho\\do\\New Cycle"')
    else:
        print("Jogo:", game)
        print(aplicar(game) if modo == "aplicar" else restaurar(game))
    try:
        input("\nEnter para sair...")
    except EOFError:
        pass


if __name__ == "__main__":
    main()
