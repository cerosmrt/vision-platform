"""Carga los trabajos de la vidriera y los rubros con su plantilla de mail.

Se corre una vez: `python seed.py`. No duplica — saltea lo que ya existe por nombre.
"""

from app import app
from models import Rubro, Trabajo, db, slugify

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
        "url": "https://momentoseterea.com/",
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


# El mail de oferta es siempre el mismo salvo por lo que se le ofrece a cada rubro.
# Lo único que cambia son los puntos del medio, así que el resto vive una sola vez acá.
CUERPO = """\
Hola, soy Federico de VISION. Les escribo para ofrecerles mis servicios como desarrollador freelance. Ayudo a negocios a tener una presencia online propia, con una web profesional y un panel administrativo para gestionar fácilmente su contenido.

Para su rubro, por ejemplo, pensé en una web donde puedan:

{puntos}

Esta es solo una idea inicial; el proyecto puede adaptarse completamente a lo que necesiten y a la forma en que trabajan actualmente.

Si quieren, pueden responder este breve formulario para contarme qué les gustaría tener. Con esa información puedo entender mejor sus necesidades y enviarles una propuesta detallada:

https://forms.gle/ybm4bhhXbZYTPJcV6

Cualquier duda, pueden escribirme al 3444568885."""


def plantilla(puntos):
    return CUERPO.format(puntos="\n".join(f"• {p}" for p in puntos))


# Lo que le sirve a cada rubro. Es la base: el mail de cada negocio se retoca después.
RUBROS = [
    (
        "Automotores",
        [
            "Publicar los vehículos con fotos, características, precio y demás información.",
            "Incorporar filtros por estado (nuevo/usado), año y rango de precio.",
            "Tener un botón de WhatsApp para consultar directamente por cada vehículo.",
            "Contar con un panel administrativo para cargar fotos, modificar precios y actualizar la información.",
            "Cargar y actualizar vehículos rápidamente desde Excel.",
        ],
    ),
    (
        "Panificados",
        [
            "Mostrar los productos con foto, descripción y precio, separados por categoría.",
            "Recibir pedidos por encargo desde la web, con fecha y hora de retiro.",
            "Armar la lista del día y marcar lo que se agotó desde el panel.",
            "Preparar el catálogo de temporada (Pascua, fiestas, cumpleaños) y publicarlo cuando quieran.",
            "Tener un botón de WhatsApp para consultar por cada producto.",
        ],
    ),
    (
        "Farmacia",
        [
            "Mostrar lo que tienen además de los medicamentos: dermocosmética, cuidado personal, bebés.",
            "Recibir pedidos y consultas por receta desde la web, sin que el cliente tenga que llamar.",
            "Publicar horarios, turnos de guardia y qué obras sociales atienden, actualizados por ustedes.",
            "Anunciar las promociones vigentes y cambiarlas desde el panel cuando quieran.",
            "Tener un botón de WhatsApp para consultar por disponibilidad.",
        ],
    ),
    (
        "Joyería",
        [
            "Mostrar cada pieza con fotos grandes, material, medidas y precio.",
            "Separar el catálogo por tipo de pieza y por material (oro, plata, acero).",
            "Recibir consultas por pieza y pedidos de trabajos a medida o arreglos.",
            "Cargar las piezas nuevas ustedes mismos desde el panel, sin depender de nadie.",
            "Tener un botón de WhatsApp para consultar directamente por cada pieza.",
        ],
    ),
    (
        "Pinturería",
        [
            "Publicar el catálogo por marca, tipo de producto y presentación, con precio.",
            "Mostrar la carta de colores para que el cliente llegue sabiendo qué quiere.",
            "Recibir pedidos y pedidos de presupuesto por obra desde la web.",
            "Actualizar precios y stock desde el panel, o cargarlos de una desde Excel.",
            "Tener un botón de WhatsApp para consultar por disponibilidad.",
        ],
    ),
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

        rubros = 0
        for nombre, puntos in RUBROS:
            if Rubro.query.filter_by(slug=slugify(nombre)).first():
                continue
            db.session.add(
                Rubro(
                    nombre=nombre,
                    slug=slugify(nombre),
                    plantilla_mail=plantilla(puntos),
                    que_ofrecer="\n".join(puntos),
                )
            )
            rubros += 1
        db.session.commit()
        print(f"Rubros creados: {rubros} (total: {Rubro.query.count()})")


if __name__ == "__main__":
    main()
