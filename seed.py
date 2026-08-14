"""Carga los trabajos ya hechos en la vidriera.

Se corre una vez: `python seed.py`. No duplica — saltea lo que ya existe por nombre.
"""

from app import app
from models import Trabajo, db

TRABAJOS = [
    {
        "nombre": "Moret Inmobiliaria",
        "bajada": "Sitio público, back-office y un mapa de 13.761 parcelas.",
        "descripcion": (
            "Reemplazó una carpeta impresa de propiedades. Tiene la web de cara al "
            "cliente, la gestión interna de propiedades, personas y consultas, y un "
            "cockpit catastral para salir a buscar terrenos antes que la competencia."
        ),
        "stack": "Flask · Postgres · Leaflet",
        "url": "https://moretinmobiliaria.com",
        "orden": 1,
    },
    {
        "nombre": "Etérea",
        "bajada": "Tienda de cosmética natural, de la vidriera al pago.",
        "descripcion": (
            "Catálogo, carrito, checkout con Mercado Pago, descuento de stock, envíos "
            "por zona y panel de administración. Pensada como una casa, no como un "
            "e-commerce."
        ),
        "stack": "Next.js · TypeScript · Firebase · Mercado Pago",
        "url": "",
        "orden": 2,
    },
    {
        "nombre": "Huellas Limpias",
        "bajada": "El sistema que reemplazó el cuaderno de ventas.",
        "descripcion": (
            "Gestión comercial completa: ventas, inventario con stock, descuentos, "
            "medios de pago, caja diaria, personal con ganancia neta y retiros, y "
            "exportación a Excel."
        ),
        "stack": "React · Firebase",
        "url": "",
        "orden": 3,
    },
]


def main():
    with app.app_context():
        db.create_all()
        creados = 0
        for datos in TRABAJOS:
            if Trabajo.query.filter_by(nombre=datos["nombre"]).first():
                continue
            db.session.add(Trabajo(**datos, publicado=True))
            creados += 1
        db.session.commit()
        print(f"Trabajos creados: {creados} (total: {Trabajo.query.count()})")


if __name__ == "__main__":
    main()
