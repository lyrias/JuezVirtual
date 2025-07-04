from app.models import Concurso, db
from werkzeug.security import generate_password_hash

def crear_concurso(form, usuario_id):
    concurso = Concurso(
        nombre=form.nombre.data,
        descripcion=form.descripcion.data,
        fecha_inicio=form.fecha_inicio.data,
        fecha_fin=form.fecha_fin.data,
        es_publico=form.es_publico.data,
        creado_por=usuario_id
    )

    if not concurso.es_publico and form.password.data:
        concurso.set_password(form.password.data)

    db.session.add(concurso)
    db.session.commit()
