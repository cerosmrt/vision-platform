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


# Las preguntas del brief, en orden. La clave es el campo en el modelo.
# Se recorren de a una en el formulario público y se muestran juntas en el admin.
PREGUNTAS_BRIEF = [
    ("negocio", "¿Cómo se llama tu negocio?", None),
    ("que_hace", "¿Qué hacés?", "En una frase, como se lo contarías a alguien en la calle."),
    ("a_quien", "¿A quién le vendés?", "Quién es la persona que te compra. Cuanto más concreto, mejor."),
    ("por_que_vos", "¿Por qué te eligen a vos y no al de al lado?", "Aunque te parezca obvio."),
    ("como_habla", "Si tu marca fuera una persona, ¿cómo hablaría?", "Formal, cercana, seria, divertida, callada."),
    ("referencias", "¿Qué marcas te gustan?", "De cualquier rubro. No hace falta que se parezcan a lo tuyo."),
    ("que_no", "¿Qué NO querés parecer?", "A veces esto define más que lo anterior."),
    ("colores", "¿Hay colores que sentís tuyos?", "Los que ya usás, o los que te gustaría usar. Si no sabés, dejalo vacío."),
    ("que_tiene_hoy", "¿Qué tenés hoy?", "Instagram, una web vieja, nada. Pasame los links si hay."),
    ("que_busca", "¿Qué querés que haga el que entra?", "Que te escriba, que compre, que vaya al local, que te conozca."),
]


class Brief(db.Model):
    """Lo que llega por el formulario público.

    No es un "contacto": son las respuestas de marca del interesado. Es la materia
    prima para entender su visión antes de expresarla en código y color.
    Se puede convertir en Negocio para entrar al pipeline.
    """

    __tablename__ = "brief"

    id = db.Column(db.Integer, primary_key=True)

    # Contacto
    nombre = db.Column(db.String(200))
    email = db.Column(db.String(200))
    telefono = db.Column(db.String(80))

    # Marca — un campo por pregunta de PREGUNTAS_BRIEF
    negocio = db.Column(db.String(200))
    que_hace = db.Column(db.Text)
    a_quien = db.Column(db.Text)
    por_que_vos = db.Column(db.Text)
    como_habla = db.Column(db.Text)
    referencias = db.Column(db.Text)
    que_no = db.Column(db.Text)
    colores = db.Column(db.Text)
    que_tiene_hoy = db.Column(db.Text)
    que_busca = db.Column(db.Text)

    leido = db.Column(db.Boolean, default=False)
    negocio_id = db.Column(db.Integer, db.ForeignKey("negocio.id"))
    creado_en = db.Column(db.DateTime, default=ahora)

    @property
    def respuestas(self):
        """Las preguntas contestadas, en orden, para mostrar en el admin."""
        return [
            (pregunta, getattr(self, campo))
            for campo, pregunta, _ in PREGUNTAS_BRIEF
            if getattr(self, campo)
        ]

    def as_dict(self):
        datos = {
            "id": self.id,
            "nombre": self.nombre,
            "email": self.email,
            "telefono": self.telefono,
            "leido": self.leido,
            "negocio_id": self.negocio_id,
            "creado_en": self.creado_en.isoformat() if self.creado_en else None,
        }
        for campo, _, _ in PREGUNTAS_BRIEF:
            datos[campo] = getattr(self, campo)
        return datos
