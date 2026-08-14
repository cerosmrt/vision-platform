# CLAUDE.md — Visión

Contexto para cualquier sesión de Claude Code que trabaje acá. Leer antes de tocar código.

## Cómo trabajamos (regla de colaboración — LO MÁS IMPORTANTE)

1. **Federico tira una idea.** No la asumo terminada ni la interpreto por mi cuenta.
2. **Recapitulo preguntando.** Preguntas **de a una por vez** y **multiple choice**
   (herramienta `AskUserQuestion`). Una pregunta, espero respuesta, siguiente pregunta.
   Nunca tirar una lista de cinco preguntas juntas.
3. **Con la respuesta, implemento.** Recién ahí se toca código.
4. **Se trabaja en bulk.** Piezas grandes y completas, no cambios de a gotas. Primero que
   exista y funcione entero; el recorte viene después.
5. **Después se hace el trim.** Una vez que la parte grande anda, se poda: sacar lo que
   sobra, simplificar, unificar.
6. **Commit después de cada función o característica terminada**, antes de seguir con la
   siguiente. No acumular varias sin commitear — cada paso queda revertible por separado.
   Mensajes en español, en imperativo, explicando el *por qué*.

Federico prefiere **respuestas breves**. Dos o tres líneas: qué hiciste y qué hay que saber.
Nada de informes largos ni de opciones que no pidió. El detalle va al commit.

## Qué es Visión

La marca y empresa de desarrollo de **Federico Moret**. Base en Gualeguay, Entre Ríos,
Argentina — pero el trabajo no es solo local.

El nombre viene de la propuesta: ayudar al dueño de una marca a traducir **la visión de su
negocio** en algo real y online.

Se ofrece desarrollo completo, front y back: sitios institucionales, catálogos, tiendas
online con pagos, y sistemas de gestión a medida. Clientes: PyMEs, desarrolladoras,
profesionales y particulares. Sin límite de rubro ni de zona.

**Todo se hace a medida, no con plantillas.** Es una restricción real, no un slogan: si una
decisión empuja hacia "esto sirve para cualquier negocio", va en contra de la propuesta.

## Qué es esta plataforma

Dos caras en una misma app:

- **Front público — la vidriera.** Muestra y linkea los trabajos hechos por Federico. Son
  links a los sitios reales; las páginas de clientes **no** se alojan acá. Incluye un
  formulario donde un interesado deja sus datos.
- **Back privado — el CRM de prospección.** Base de datos de posibles clientes. Federico
  investiga cada negocio, redacta el mail, lo manda y sigue la respuesta.

Los leads entran por dos lados: los que llegan solos por el formulario y los que carga
Federico al salir a buscar.

### Decisiones ya tomadas

- **El mail no sale de la plataforma.** La plataforma lo redacta; Federico copia, pega y
  manda desde su cuenta. Evita dominio, autenticación de envío y riesgo de spam. Se puede
  revisar más adelante.
- **La investigación automática va después de la manual.** Primero cargar negocios a mano.
  Hasta no usar el CRM de verdad no se sabe qué campos conviene llenar solos; automatizar
  antes es automatizar lo imaginado.

## Trabajos hechos (la vidriera)

Tres plataformas ya construidas, cada una con un stack distinto:

| Trabajo | Qué es | Stack | Estado |
|---|---|---|---|
| **Moret Inmobiliaria** | Sitio público + back-office: propiedades, leads, consultas, cockpit catastral con Leaflet sobre 13.761 parcelas | Flask + Postgres + Jinja + JS vanilla, Railway + Cloudflare | **Online** en moretinmobiliaria.com |
| **Etérea** | Ecommerce completo: catálogo, carrito, checkout, Mercado Pago, stock, envíos por zona, panel admin | Next.js 16 + TS + Tailwind v4 + Firebase | Desarrollado, **no levantado** |
| **Huellas Limpias** | Sistema de gestión comercial multi-tenant: ventas, inventario, caja, personal, export a Excel | React 19 + Firebase | **Local**, no publicado |

Código en `z:\programming\Dad`, `z:\programming\Eterea_Pagina_Web` y
`z:\programming\commerce-administrator`.

## Stack de esta plataforma

**Flask + SQLAlchemy + Postgres + Jinja + JS vanilla.** Elegido por lo que pide este
proyecto:

- El peso está en el backend, no en el front. La vidriera son pocas páginas casi estáticas;
  lo complejo es la investigación (traer datos del negocio, parsear, llamar a la API de
  Claude para diagnosticar y redactar). Eso es trabajo de Python.
- Los datos son relacionales de verdad: negocio → contactos → actividades → envíos. Las
  consultas útiles son tipo "gastronómicos contactados hace más de 7 días sin respuesta" —
  una línea de SQL. Firestore hace mal exactamente este caso.
- Va a haber trabajo en segundo plano: investigar en bulk no puede correr con el usuario
  esperando. En Python es un script y un cron.

Concreto:

- **Backend:** Flask 3 + Flask-SQLAlchemy + Flask-Migrate/Alembic.
- **DB:** SQLite en dev (`instance/vision.db`), Postgres en prod vía `DATABASE_URL`.
- **Frontend:** Jinja2 + JS vanilla, sin build step ni framework.
- **IA:** API de Claude para diagnóstico y redacción de mails. No se entrenan modelos.

## Estructura

```
app.py              Rutas: sitio público, admin y APIs JSON
models.py           Admin, Trabajo, Negocio, Contacto, Actividad, Consulta
config.py           DevelopmentConfig (SQLite) / ProductionConfig (Postgres)
templates/
  base.html         Layout público
  index.html        Vidriera: hero, servicios, trabajos, formulario
  admin/
    base.html       Layout admin (lateral + main)
    login.html      Pantalla de login
    index.html      Pipeline de prospección: conteos, filtros, tabla
    negocio.html    Ficha: datos, diagnóstico, borrador de mail, contactos, historial
    consultas.html  Bandeja del formulario público
    trabajos.html   ABM de la vidriera
static/
  public.css        Estilos del sitio público
  admin.css         Design system del admin
  admin.js          Wrapper `api()` de fetch (inyecta CSRF, maneja 401) + `esc()`
```

## Comandos

```bash
venv\Scripts\activate           # Windows
pip install -r requirements.txt
copy .env.example .env          # completar SECRET_KEY y ADMIN_PASSWORD

python app.py                   # http://localhost:5000 · admin en /admin
```

La primera vez, `app.py` crea las tablas y el admin de `.env` automáticamente.

## Convenciones del código

- Cada modelo expone **`as_dict()`** para serializar a JSON.
- Auth por decoradores: **`@login_required`** (páginas, redirige al login) y
  **`@api_login_required`** (API, 401 JSON + verifica **CSRF** con `hmac.compare_digest`
  en los métodos que mutan).
- **Soft-delete** con `deleted_at` en `Negocio`; las queries filtran `deleted_at IS NULL`.
- `_campos(modelo, datos, permitidos)` copia solo campos de una lista blanca. Nunca asignar
  desde el request directo.
- Front admin: todo el fetch pasa por `api()` en `admin.js`. Usar `esc()` para escapar HTML.

## Voz y tono

Todo lo de cara al cliente va en **español rioplatense**:

- De "vos", nunca de "tú".
- Directo y concreto. Al cliente no le importa el stack, le importa qué gana.
- Sin inflar. Nada de "soluciones digitales de vanguardia".
- En mensajes de venta: un gancho **específico de ese negocio**. Si el mensaje le sirve
  igual a cualquiera, está mal escrito.

## Reglas duras

- **Nunca contactar a un cliente ni potencial cliente por mi cuenta.** Redacto; Federico
  manda.
- **Los datos de contacto que encuentro son sugerencias.** Verificar antes de usar: los
  perfiles de negocios locales quedan desactualizados seguido.
- **No nombrar clientes en mails de oferta.** Decisión tomada: el primer mail es oferta de
  servicio, sin casos ni nombres.
- **Sin precios en el primer mail.** El precio va después de la charla.
- **Separación pública vs admin es real.** Templates, rutas y decoradores distintos. Nunca
  exponer datos internos en la vista pública.
