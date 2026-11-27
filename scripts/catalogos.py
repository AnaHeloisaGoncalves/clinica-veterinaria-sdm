"""Carga aditiva de espécies e raças: python -m scripts.catalogos."""
from api_clinica.db import database, query, write


# Nomes comuns para seleção no cadastro clínico.
ESPECIES = {
    "Cão": "Mamífero — animal de companhia.",
    "Gato": "Mamífero — animal de companhia.",
    "Coelho doméstico": "Mamífero — lagomorfo.",
    "Porquinho-da-índia": "Mamífero — roedor.",
    "Hamster-sírio": "Mamífero — roedor.",
    "Hamster-anão-russo": "Mamífero — roedor.",
    "Gerbil-da-mongólia": "Mamífero — roedor.",
    "Chinchila": "Mamífero — roedor.",
    "Rato doméstico": "Mamífero — roedor.",
    "Camundongo doméstico": "Mamífero — roedor.",
    "Furão doméstico": "Mamífero — mustelídeo.",
    "Ouriço-pigmeu-africano": "Mamífero — ouriço.",
    "Gambá-de-orelha-branca": "Mamífero — marsupial.",
    "Gambá-de-orelha-preta": "Mamífero — marsupial.",
    "Sagui-de-tufo-branco": "Mamífero — primata.",
    "Calopsita": "Ave — psitacídeo.",
    "Periquito-australiano": "Ave — psitacídeo.",
    "Agapornis-roseicollis": "Ave — psitacídeo.",
    "Papagaio-verdadeiro": "Ave — psitacídeo.",
    "Papagaio-do-mangue": "Ave — psitacídeo.",
    "Arara-canindé": "Ave — psitacídeo.",
    "Maritaca": "Ave — nome comum; detalhar a identificação na ficha.",
    "Canário-do-reino": "Ave — passeriforme.",
    "Diamante-mandarim": "Ave — passeriforme.",
    "Pombo-doméstico": "Ave — columbiforme.",
    "Galinha doméstica": "Ave — galiforme.",
    "Codorna-japonesa": "Ave — galiforme.",
    "Pato doméstico": "Ave — nome comum; detalhar a identificação na ficha.",
    "Jabuti-piranga": "Réptil — quelônio terrestre.",
    "Jabuti-tinga": "Réptil — quelônio terrestre.",
    "Tigre-d'água-brasileiro": "Réptil — quelônio semiaquático.",
    "Iguana-verde": "Réptil — lagarto.",
    "Dragão-barbudo": "Réptil — lagarto.",
    "Gecko-leopardo": "Réptil — lagarto.",
    "Teiú": "Réptil — nome comum; detalhar a identificação na ficha.",
    "Jiboia": "Réptil — serpente.",
    "Cobra-do-milho": "Réptil — serpente.",
    "Píton-real": "Réptil — serpente.",
}


# SRD é uma opção de cadastro, não uma raça reconhecida.
RACAS = {
    "Cão": (
        "Sem raça definida (SRD)", "Labrador", "Golden Retriever", "Shih Tzu",
        "Yorkshire Terrier", "Poodle", "Spitz Alemão", "Bulldog Francês",
        "Bulldog Inglês", "Pug", "Beagle", "Dachshund", "Pinscher Miniatura",
        "Chihuahua", "Maltês", "Lhasa Apso", "Border Collie", "Pastor Alemão",
        "Rottweiler", "Boxer", "Husky Siberiano", "Schnauzer Miniatura",
        "Cocker Spaniel Inglês", "Cavalier King Charles Spaniel", "Boston Terrier",
        "Basset Hound", "Dálmata", "Dobermann", "Chow Chow", "Akita",
        "Shiba Inu", "American Pit Bull Terrier", "American Staffordshire Terrier",
        "Bull Terrier", "Fila Brasileiro", "Weimaraner", "Dogue Alemão",
        "São Bernardo", "Pastor Australiano", "Cane Corso",
    ),
    "Gato": (
        "Sem raça definida (SRD)", "Siamês", "Persa", "Maine Coon", "Ragdoll",
        "Bengal", "British Shorthair", "Scottish Fold", "Sphynx",
        "Exótico de Pelo Curto", "Angorá Turco", "Azul Russo", "Abissínio",
        "Sagrado da Birmânia", "Norueguês da Floresta", "Siberiano",
        "American Shorthair", "Oriental de Pelo Curto", "Devon Rex", "Himalaio",
    ),
}


def carregar_catalogos(db):
    """Preserva registros existentes, inclusive os inativos, sem duplicar nomes."""
    especies_adicionadas = 0
    racas_adicionadas = 0
    for especie, descricao in ESPECIES.items():
        rows = query(db, "SELECT id FROM especie WHERE nome = %s ORDER BY id", (especie,))
        if rows:
            especie_id = rows[0]["id"]
        else:
            especie_id = write(
                db, "INSERT INTO especie (nome, descricao) VALUES (%s, %s)",
                (especie, descricao),
            )[0]
            especies_adicionadas += 1
        for raca in RACAS.get(especie, ()):
            if not query(db, "SELECT id FROM raca WHERE nome = %s AND especie_id = %s", (raca, especie_id)):
                write(db, "INSERT INTO raca (nome, especie_id) VALUES (%s, %s)", (raca, especie_id))
                racas_adicionadas += 1
    return especies_adicionadas, racas_adicionadas


def main():
    gen = database()
    db = next(gen)
    try:
        especies, racas = carregar_catalogos(db)
        db.commit()
        print(f"Catálogo atualizado: {especies} espécies e {racas} raças adicionadas.")
    finally:
        gen.close()


if __name__ == "__main__":
    main()
