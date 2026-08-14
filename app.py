import hmac
import secrets
from datetime import datetime, timezone
from functools import wraps

from flask import (
    Flask,
    abort,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_migrate import Migrate

from config import get_config
from models import (
    ESTADOS,
    PREGUNTAS_BRIEF,
    TIPOS_ACTIVIDAD,
    Actividad,
    Admin,
    Brief,
    Contacto,
    Negocio,
    Trabajo,
    ahora,
    db,
)

app = Flask(__name__)
app.config.from_object(get_config())
db.init_app(app)
migrate = Migrate(app, db)


# --------------------------------------------------------------------------
# Auth
# --------------------------------------------------------------------------

def login_required(f):
    """Para páginas: si no hay sesión, manda al login."""

    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("admin_id"):
            return redirect(url_for("admin_login", next=request.path))
        return f(*args, **kwargs)

    return wrapper


def api_login_required(f):
    """Para APIs: 401 JSON, y verifica CSRF en métodos que mutan."""

    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("admin_id"):
            return jsonify({"error": "no autorizado"}), 401
        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            enviado = request.headers.get("X-CSRFToken", "")
            if not hmac.compare_digest(enviado, session.get("csrf_token", "")):
                return jsonify({"error": "csrf invalido"}), 403
        return f(*args, **kwargs)

    return wrapper


@app.context_processor
def inyectar_globales():
    return {
        "csrf_token": session.get("csrf_token", ""),
        "estados": ESTADOS,
        "tipos_actividad": TIPOS_ACTIVIDAD,
        "anio": datetime.now().year,
    }


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def _campos(modelo, datos, campos):
    """Copia solo los campos permitidos desde un dict al modelo."""
    for campo in campos:
        if campo in datos:
            valor = datos[campo]
            if isinstance(valor, str):
                valor = valor.strip() or None
            setattr(modelo, campo, valor)


def negocio_o_404(negocio_id):
    negocio = db.session.get(Negocio, negocio_id)
    if not negocio or negocio.deleted_at:
        abort(404)
    return negocio


CAMPOS_NEGOCIO = [
    "nombre", "rubro", "ciudad", "provincia", "web", "instagram",
    "facebook", "email", "telefono", "estado", "diagnostico",
    "borrador_mail", "notas",
]

CAMPOS_BRIEF = ["nombre", "email", "telefono"] + [c for c, _, _ in PREGUNTAS_BRIEF]


# --------------------------------------------------------------------------
# Sitio público — la vidriera
# --------------------------------------------------------------------------

@app.route("/")
def home():
    trabajos = (
        Trabajo.query.filter_by(publicado=True)
        .order_by(Trabajo.orden, Trabajo.id)
        .all()
    )
    return render_template("index.html", trabajos=trabajos)


@app.route("/formulario")
def formulario():
    return render_template("formulario.html", preguntas=PREGUNTAS_BRIEF)


@app.route("/api/public/brief", methods=["POST"])
def crear_brief():
    datos = request.get_json(silent=True) or request.form
    if not (datos.get("nombre") or datos.get("email")):
        return jsonify({"error": "faltan datos"}), 400

    brief = Brief()
    _campos(brief, datos, CAMPOS_BRIEF)
    db.session.add(brief)
    db.session.commit()
    return jsonify({"ok": True}), 201


# --------------------------------------------------------------------------
# Admin — login
# --------------------------------------------------------------------------

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    error = None
    if request.method == "POST":
        admin = Admin.query.filter_by(email=request.form.get("email", "").strip()).first()
        if admin and admin.check_password(request.form.get("password", "")):
            session["admin_id"] = admin.id
            session["csrf_token"] = secrets.token_urlsafe(32)
            return redirect(request.args.get("next") or url_for("admin_index"))
        error = "Email o contraseña incorrectos."
    return render_template("admin/login.html", error=error)


@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))


# --------------------------------------------------------------------------
# Admin — pipeline de prospección
# --------------------------------------------------------------------------

@app.route("/admin")
@login_required
def admin_index():
    query = Negocio.query.filter(Negocio.deleted_at.is_(None))

    estado = request.args.get("estado")
    if estado:
        query = query.filter_by(estado=estado)
    rubro = request.args.get("rubro")
    if rubro:
        query = query.filter_by(rubro=rubro)
    buscar = request.args.get("q")
    if buscar:
        query = query.filter(Negocio.nombre.ilike(f"%{buscar}%"))

    negocios = query.order_by(Negocio.actualizado_en.desc()).all()

    conteos = {clave: 0 for clave, _ in ESTADOS}
    for n in Negocio.query.filter(Negocio.deleted_at.is_(None)).all():
        conteos[n.estado] = conteos.get(n.estado, 0) + 1

    rubros = sorted(
        {n.rubro for n in Negocio.query.filter(Negocio.rubro.isnot(None)).all()}
    )
    sin_leer = Brief.query.filter_by(leido=False).count()

    return render_template(
        "admin/index.html",
        negocios=negocios,
        conteos=conteos,
        rubros=rubros,
        sin_leer=sin_leer,
        filtros={"estado": estado, "rubro": rubro, "q": buscar},
    )


@app.route("/admin/negocio/<int:negocio_id>")
@login_required
def admin_negocio(negocio_id):
    return render_template("admin/negocio.html", negocio=negocio_o_404(negocio_id))


@app.route("/admin/briefs")
@login_required
def admin_briefs():
    briefs = Brief.query.order_by(Brief.creado_en.desc()).all()
    return render_template("admin/briefs.html", briefs=briefs)


@app.route("/admin/trabajos")
@login_required
def admin_trabajos():
    trabajos = Trabajo.query.order_by(Trabajo.orden, Trabajo.id).all()
    return render_template("admin/trabajos.html", trabajos=trabajos)


# --------------------------------------------------------------------------
# API admin — negocios
# --------------------------------------------------------------------------

@app.route("/api/negocios", methods=["POST"])
@api_login_required
def api_crear_negocio():
    datos = request.get_json(silent=True) or {}
    if not (datos.get("nombre") or "").strip():
        return jsonify({"error": "el nombre es obligatorio"}), 400

    negocio = Negocio()
    _campos(negocio, datos, CAMPOS_NEGOCIO)
    negocio.estado = negocio.estado or "sin_investigar"
    db.session.add(negocio)
    db.session.commit()
    return jsonify(negocio.as_dict()), 201


@app.route("/api/negocios/<int:negocio_id>", methods=["PATCH"])
@api_login_required
def api_editar_negocio(negocio_id):
    negocio = negocio_o_404(negocio_id)
    datos = request.get_json(silent=True) or {}
    estado_previo = negocio.estado

    _campos(negocio, datos, CAMPOS_NEGOCIO)

    # Pasar a "contactado" sella la fecha, que es lo que después ordena el seguimiento.
    if negocio.estado == "contactado" and estado_previo != "contactado":
        negocio.contactado_en = ahora()
        db.session.add(
            Actividad(negocio_id=negocio.id, tipo="mail", detalle="Marcado como contactado")
        )

    db.session.commit()
    return jsonify(negocio.as_dict())


@app.route("/api/negocios/<int:negocio_id>", methods=["DELETE"])
@api_login_required
def api_borrar_negocio(negocio_id):
    negocio = negocio_o_404(negocio_id)
    negocio.deleted_at = ahora()
    db.session.commit()
    return jsonify({"ok": True})


@app.route("/api/negocios/<int:negocio_id>/actividades", methods=["POST"])
@api_login_required
def api_crear_actividad(negocio_id):
    negocio = negocio_o_404(negocio_id)
    datos = request.get_json(silent=True) or {}
    actividad = Actividad(
        negocio_id=negocio.id,
        tipo=datos.get("tipo") or "nota",
        detalle=(datos.get("detalle") or "").strip() or None,
    )
    db.session.add(actividad)
    db.session.commit()
    return jsonify(actividad.as_dict()), 201


@app.route("/api/negocios/<int:negocio_id>/contactos", methods=["POST"])
@api_login_required
def api_crear_contacto(negocio_id):
    negocio = negocio_o_404(negocio_id)
    datos = request.get_json(silent=True) or {}
    contacto = Contacto(negocio_id=negocio.id)
    _campos(contacto, datos, ["nombre", "rol", "email", "telefono"])
    db.session.add(contacto)
    db.session.commit()
    return jsonify(contacto.as_dict()), 201


@app.route("/api/contactos/<int:contacto_id>", methods=["DELETE"])
@api_login_required
def api_borrar_contacto(contacto_id):
    contacto = db.session.get(Contacto, contacto_id)
    if not contacto:
        abort(404)
    db.session.delete(contacto)
    db.session.commit()
    return jsonify({"ok": True})


# --------------------------------------------------------------------------
# API admin — briefs y trabajos
# --------------------------------------------------------------------------

@app.route("/api/briefs/<int:brief_id>/leido", methods=["PATCH"])
@api_login_required
def api_marcar_leido(brief_id):
    brief = db.session.get(Brief, brief_id)
    if not brief:
        abort(404)
    brief.leido = True
    db.session.commit()
    return jsonify(brief.as_dict())


@app.route("/api/briefs/<int:brief_id>/convertir", methods=["POST"])
@api_login_required
def api_convertir_brief(brief_id):
    """Un brief del formulario pasa a ser un negocio del pipeline.

    Las respuestas de marca se vuelcan al diagnóstico: es lo que el interesado
    contó de sí mismo, y es de donde arranca la propuesta.
    """
    brief = db.session.get(Brief, brief_id)
    if not brief:
        abort(404)
    if brief.negocio_id:
        return jsonify({"error": "ya fue convertido"}), 400

    diagnostico = "\n\n".join(f"{p}\n{r}" for p, r in brief.respuestas)

    negocio = Negocio(
        nombre=brief.negocio or brief.nombre or "Sin nombre",
        email=brief.email,
        telefono=brief.telefono,
        origen="formulario",
        estado="respondio",
        diagnostico=diagnostico or None,
    )
    db.session.add(negocio)
    db.session.flush()

    if brief.nombre:
        db.session.add(
            Contacto(negocio_id=negocio.id, nombre=brief.nombre,
                     email=brief.email, telefono=brief.telefono)
        )
    db.session.add(
        Actividad(negocio_id=negocio.id, tipo="nota",
                  detalle="Llenó el formulario de marca del sitio")
    )
    brief.negocio_id = negocio.id
    brief.leido = True
    db.session.commit()
    return jsonify(negocio.as_dict()), 201


@app.route("/api/trabajos", methods=["POST"])
@api_login_required
def api_crear_trabajo():
    datos = request.get_json(silent=True) or {}
    if not (datos.get("nombre") or "").strip():
        return jsonify({"error": "el nombre es obligatorio"}), 400
    trabajo = Trabajo()
    _campos(trabajo, datos, ["nombre", "bajada", "descripcion", "stack", "url", "imagen"])
    trabajo.orden = datos.get("orden") or 0
    trabajo.publicado = bool(datos.get("publicado", True))
    db.session.add(trabajo)
    db.session.commit()
    return jsonify(trabajo.as_dict()), 201


@app.route("/api/trabajos/<int:trabajo_id>", methods=["PATCH"])
@api_login_required
def api_editar_trabajo(trabajo_id):
    trabajo = db.session.get(Trabajo, trabajo_id)
    if not trabajo:
        abort(404)
    datos = request.get_json(silent=True) or {}
    _campos(trabajo, datos, ["nombre", "bajada", "descripcion", "stack", "url", "imagen"])
    if "orden" in datos:
        trabajo.orden = datos["orden"] or 0
    if "publicado" in datos:
        trabajo.publicado = bool(datos["publicado"])
    db.session.commit()
    return jsonify(trabajo.as_dict())


@app.route("/api/trabajos/<int:trabajo_id>", methods=["DELETE"])
@api_login_required
def api_borrar_trabajo(trabajo_id):
    trabajo = db.session.get(Trabajo, trabajo_id)
    if not trabajo:
        abort(404)
    db.session.delete(trabajo)
    db.session.commit()
    return jsonify({"ok": True})


# --------------------------------------------------------------------------
# Arranque
# --------------------------------------------------------------------------

def crear_admin_inicial():
    """Crea el admin de la config si todavía no hay ninguno."""
    if Admin.query.first():
        return
    email = app.config.get("ADMIN_EMAIL")
    password = app.config.get("ADMIN_PASSWORD")
    if not (email and password):
        return
    admin = Admin(email=email)
    admin.set_password(password)
    db.session.add(admin)
    db.session.commit()
    print(f"Admin inicial creado: {email}")


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        crear_admin_inicial()
    app.run(debug=app.config.get("DEBUG", False), port=5000)
