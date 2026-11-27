import re
from datetime import date
from unicodedata import normalize

from pydantic import BeforeValidator
from typing import Annotated

LIMITE_TUTOR_ANOS = 120
LIMITE_ANIMAL_PADRAO_ANOS = 120
LIMITES_ANIMAL_ANOS = {
    "cao": 35, "gato": 40, "coelho domestico": 20, "porquinho-da-india": 15,
    "hamster sirio": 6, "hamster anao-russo": 6, "chinchila": 30, "ferret": 18,
    "rato domestico": 7, "gerbil": 8, "calopsita": 40, "periquito-australiano": 25,
    "canario-belga": 25, "diamante-mandarim": 15, "agapornis roseicollis": 30,
    "papagaio-verdadeiro": 100, "arara-caninde": 100, "maritaca": 60, "tucano-toco": 40,
    "jabuti-piranga": 150, "jabuti-tinga": 150, "tigre-d'agua": 80, "iguana-verde": 35,
    "gecko-leopardo": 35, "dragao-barbudo": 25, "jiboia": 55, "corn snake": 35, "axolote": 30,
}


def chave_especie(nome):
    return "".join(c for c in normalize("NFKD", nome.strip().casefold()) if c.isascii())


def idade_meses(nascimento, hoje):
    return (hoje.year - nascimento.year) * 12 + hoje.month - nascimento.month - (hoje.day < nascimento.day)


def formato_nascimento(valor):
    if valor is not None and type(valor) is not date and (
        not isinstance(valor, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", valor)
    ):
        raise ValueError("Informe uma data de nascimento no formato AAAA-MM-DD")
    return valor


Nascimento = Annotated[date, BeforeValidator(formato_nascimento)]


def validar_nascimento_tutor(nascimento):
    meses = idade_meses(nascimento, date.today())
    if not 0 <= meses <= LIMITE_TUTOR_ANOS * 12:
        raise ValueError(f"Informe uma data de nascimento entre hoje e {LIMITE_TUTOR_ANOS} anos atrás")
    return nascimento
