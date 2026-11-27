"""Catálogo de registro. Os tipos são classificações do sistema."""
VACINAS = {
    "antirrabica": ("Antirrábica", "Antirrábica", ("cao", "gato", "ferret"), True),
    "canina-v8": ("Múltipla canina V8", "Polivalente", ("cao",), False),
    "canina-v10": ("Múltipla canina V10", "Polivalente", ("cao",), False),
    "canina-leptospirose": ("Leptospirose canina", "Leptospirose", ("cao",), False),
    "canina-bordetella": ("Bordetella canina", "Respiratória", ("cao",), False),
    "felina-v3": ("Tríplice felina V3", "Polivalente", ("gato",), False),
    "felina-v4": ("Quádrupla felina V4", "Polivalente", ("gato",), False),
    "felina-v5": ("Quíntupla felina V5", "Polivalente", ("gato",), False),
    "felina-felv": ("Leucemia felina (FeLV)", "FeLV", ("gato",), False),
    "ferret-cinomose": ("Cinomose", "Cinomose", ("ferret",), False),
}
