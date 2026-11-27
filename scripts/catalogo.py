"""Cadastra espécies e raças iniciais sem substituir registros existentes."""
from api_clinica.db import database, query, write

CATALOGO = {
    "Cão": ("Labrador", "Golden Retriever", "Shih Tzu", "Poodle", "Yorkshire Terrier",
            "Lhasa Apso", "Spitz Alemão", "Bulldog Francês", "Pinscher", "Dachshund",
            "Beagle", "Border Collie", "Pastor Alemão", "Chihuahua", "Pug", "Rottweiler"),
    "Gato": ("Siamês", "Persa", "Maine Coon", "Ragdoll", "Angorá Turco", "Sphynx",
             "British Shorthair", "Bengal"),
    "Coelho doméstico": ("Mini Lop", "Lionhead", "Holandês", "Nova Zelândia"),
    "Porquinho-da-índia": ("Americano", "Abissínio", "Peruano"),
    "Hamster sírio": (), "Hamster anão-russo": (), "Chinchila": (),
    "Ferret": (), "Rato doméstico": (), "Gerbil": (),
    "Calopsita": (), "Periquito-australiano": (), "Canário-belga": (), "Diamante-mandarim": (),
    "Agapornis roseicollis": (), "Papagaio-verdadeiro": (), "Arara-canindé": (),
    "Maritaca": (), "Tucano-toco": (), "Jabuti-piranga": (), "Jabuti-tinga": (),
    "Tigre-d'água": (), "Iguana-verde": (), "Gecko-leopardo": (), "Dragão-barbudo": (),
    "Jiboia": (), "Corn snake": (), "Axolote": (),
}


def popular(db):
    for especie, racas in CATALOGO.items():
        registros = query(db, "SELECT id FROM especie WHERE nome = %s ORDER BY id", (especie,))
        especie_id = registros[0]["id"] if registros else write(
            db, "INSERT INTO especie (nome) VALUES (%s)", (especie,)
        )[0]
        for raca in racas:
            if not query(db, "SELECT id FROM raca WHERE especie_id = %s AND nome = %s", (especie_id, raca)):
                write(db, "INSERT INTO raca (especie_id, nome) VALUES (%s, %s)", (especie_id, raca))


if __name__ == "__main__":
    conexao = database()
    try:
        db = next(conexao)
        popular(db)
        db.commit()
        print(f"Catálogo preparado: {len(CATALOGO)} espécies e {sum(map(len, CATALOGO.values()))} raças.")
    finally:
        conexao.close()
