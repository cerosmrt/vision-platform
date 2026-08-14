from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()


def ahora():
    return datetime.now(timezone.utc)


# Estados del pipeline de prospección, en orden.
ESTADOS = [
    ("sin_investigar", "Sin investigar"),
    ("investigado", "Investigado"),
    ("contactado", "Contactado"),
    ("respondio", "Respondió"),
    ("reunion", "Reunión"),
    ("cliente", "Cliente"),
    ("descartado", "Descartado"),
]
ESTADOS_DICT = dict(ESTADOS)

TIPOS_ACTIVIDAD = [
    ("nota", "Nota"),
    ("mail", "Mail"),
    ("llamada", "Llamada"),
    ("dm", "Mensaje directo"),
    ("reunion", "Reunión"),
]


class Admin(db.Model):
    __tablename__ = "admin"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200), unique=True, nullable=False)
    password_hash = db.Column(db.String(300), nullable=False)
    creado_en = db.Column(db.DateTime, default=ahora)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Trabajo(db.Model):
    """Un trabajo hecho por Federico. Es lo que se muestra en la vidriera."""

    __tablename__ = "trabajo"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), nullable=False)
    bajada = db.Column(db.String(400))
    descripcion = db.Column(db.Text)
    stack = db.Column(db.String(300))
    url = db.Column(db.String(400))
    imagen = db.Column(db.String(400))
    orden = db.Column(db.Integer, default=0)
    publicado = db.Column(db.Boolean, default=True)
    creado_en = db.Column(db.DateTime, default=ahora)

    def as_dict(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "bajada": self.bajada,
            "descripcion": self.descripcion,
            "stack": self.stack,
            "url": self.url,
            "imagen": self.imagen,
            "orden": self.orden,
            "publicado": self.publicado,
        }


class Negocio(db.Model):
    """Un posible cliente. Entra a mano (prospección) o por el formulario público."""

    __tablename__ = "negocio"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), nullable=False)
    rubro = db.Column(db.String(120))
    ciudad = db.Column(db.String(120))
    provincia = db.Column(db.String(120))

    web = db.Column(db.String(400))
    instagram = db.Column(db.String(200))
    facebook = db.Column(db.String(200))
    email = db.Column(db.String(200))
    telefono = db.Column(db.String(80))

    estado = db.Column(db.String(40), default="sin_investigar", index=True)
    origen = db.Column(db.String(40), default="manual")  # manual | formulario

    # Resultado de la investigación: qué tiene y qué le falta.
    diagnostico = db.Column(db.Text)
    # Borrador del mail de oferta. Federico lo copia y lo manda desde su cuenta.
    borrador_mail = db.Column(db.Text)
    notas = db.Column(db.Text)

    contactado_en = db.Column(db.DateTime)
    creado_en = db.Column(db.DateTime, default=ahora)
    actualizado_en = db.Column(db.DateTime, default=ahora, onupdate=ahora)
    deleted_at = db.Column(db.DateTime)

    contactos = db.relationship(
        "Contacto", backref="negocio", cascade="all, delete-orphan", lazy="selectin"
    )
    actividades = db.relationship(
        "Actividad",
        backref="negocio",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="Actividad.fecha.desc()",
    )

    @property
    def estado_label(self):
        return ESTADOS_DICT.get(self.estado, self.estado)

    @property
    def dias_desde_contacto(self):
        if not self.contactado_en:
            return None
        return (ahora() - self.contactado_en.replace(tzinfo=timezone.utc)).days

    def as_dict(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "rubro": self.rubro,
            "ciudad": self.ciudad,
            "provincia": self.provincia,
            "web": self.web,
            "instagram": self.instagram,
            "facebook": self.facebook,
            "email": self.email,
            "telefono": self.telefono,
            "estado": self.estado,
            "estado_label": self.estado_label,
            "origen": self.origen,
            "diagnostico": self.diagnostico,
            "borrador_mail": self.borrador_mail,
            "notas": self.notas,
            "dias_desde_contacto": self.dias_desde_contacto,
            "contactos": [c.as_dict() for c in self.contactos],
        }


class Contacto(db.Model):
    """Una persona dentro de un negocio."""

    __tablename__ = "contacto"

    id = db.Column(db.Integer, primary_key=True)
    negocio_id = db.Column(db.Integer, db.ForeignKey("negocio.id"), nullable=False)
    nombre = db.Column(db.String(200))
    rol = db.Column(db.String(120))
    email = db.Column(db.String(200))
    telefono = db.Column(db.String(80))

    def as_dict(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "rol": self.rol,
            "email": self.email,
            "telefono": self.telefono,
        }


class Actividad(db.Model):
    """Cada cosa que pasó con un negocio. Es el historial del seguimiento."""

    __tablename__ = "actividad"

    id = db.Column(db.Integer, primary_key=True)
    negocio_id = db.Column(db.Integer, db.ForeignKey("negocio.id"), nullable=False)
    tipo = db.Column(db.String(40), default="nota")
    detalle = db.Column(db.Text)
    fecha = db.Column(db.DateTime, default=ahora)

    def as_dict(self):
        return {
            "id": self.id,
            "tipo": self.tipo,
            "detalle": self.detalle,
            "fecha": self.fecha.isoformat() if self.fecha else None,
        }


class Consulta(db.Model):
    """Lo que llega por el formulario público. Se puede convertir en Negocio."""

    __tablename__ = "consulta"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200))
    negocio = db.Column(db.String(200))
    email = db.Column(db.String(200))
    telefono = db.Column(db.String(80))
    mensaje = db.Column(db.Text)
    leida = db.Column(db.Boolean, default=False)
    negocio_id = db.Column(db.Integer, db.ForeignKey("negocio.id"))
    creada_en = db.Column(db.DateTime, default=ahora)

    def as_dict(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "negocio": self.negocio,
            "email": self.email,
            "telefono": self.telefono,
            "mensaje": self.mensaje,
            "leida": self.leida,
            "negocio_id": self.negocio_id,
            "creada_en": self.creada_en.isoformat() if self.creada_en else None,
        }
