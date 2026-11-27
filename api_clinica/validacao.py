import re
from unicodedata import normalize

UFS = "AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO".split()
SEXOS = {"M": "Macho", "F": "Fêmea", "NI": "Não identificado"}
CORES = (
    "Branco", "Preto", "Cinza", "Marrom", "Caramelo", "Creme", "Bege", "Dourado",
    "Amarelo", "Laranja", "Vermelho", "Azul", "Verde", "Roxo", "Rosa", "Prateado",
    "Branco e preto", "Branco e marrom", "Branco e cinza", "Preto e marrom",
    "Bicolor", "Tricolor", "Tigrado", "Rajado", "Malhado", "Multicolorido",
    "Albino", "Outra coloração",
)
VIAS_VACINA = {
    "SC": "Subcutânea", "IM": "Intramuscular", "ID": "Intradérmica",
    "IN": "Intranasal", "ORAL": "Oral", "OCULAR": "Ocular",
}
CORES_VALIDAS = {cor.casefold() for cor in CORES}


def nome_valido(valor):
    valor = normalize("NFC", " ".join(valor.split()))
    partes = re.split(r"[ '’-]", valor)
    if any(not parte.isalpha() for parte in partes) or sum(map(len, partes)) < 2:
        raise ValueError("Use letras, espaços, hífen ou apóstrofo para preencher o nome")
    for parte in partes:
        palavra = parte.casefold()
        if len(palavra) >= 8 and any(
            palavra == (palavra[:periodo] * (len(palavra) // periodo + 1))[:len(palavra)]
            for periodo in range(1, len(palavra) // 2 + 1)
        ):
            raise ValueError("Revise a sequência de letras do nome")
    return valor


def uf_valida(valor):
    valor = valor.upper()
    if valor not in UFS:
        raise ValueError("Selecione uma UF brasileira válida")
    return valor
