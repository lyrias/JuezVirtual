from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, session
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import os

from app.forms import ConcursoForm
from app.models import Concurso, Problema, ConcursoProblema, db, Envio, Veredicto, Lenguaje, Concurso, Usuario
from app.concursos.concursos import crear_concurso  
from app.worker import cola_envios

from sqlalchemy import or_, func
from sqlalchemy.sql import case

from collections import defaultdict
import random

from flask_wtf import FlaskForm
from wtforms import PasswordField, SubmitField
from wtforms.validators import DataRequired

from pytz import timezone, UTC

from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash

from sqlalchemy.sql import case


concursos_bp = Blueprint('concursos', __name__, url_prefix='/concursos')

@concursos_bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_concurso():
    zona_bolivia = timezone("America/La_Paz")
    ahora = datetime.now(zona_bolivia)
    if not current_user.es_admin:
        flash('Acceso denegado. Solo los administradores pueden crear concursos.', 'danger')
        return redirect(url_for('main.dashboard'))

    form = ConcursoForm()
    if form.validate_on_submit():
        crear_concurso(form, current_user.id)
        flash('Concurso creado correctamente.', 'success')
        return redirect(url_for('concursos.lista_concursos'))

    return render_template('concursos/nuevo.html', form=form)


def crear_concurso(form, autor_id):
    tz_bolivia = timezone("America/La_Paz")

    fecha_inicio = form.fecha_inicio.data
    fecha_fin    = form.fecha_fin.data

    if fecha_inicio.tzinfo is None:
        fecha_inicio = tz_bolivia.localize(fecha_inicio)
    if fecha_fin.tzinfo is None:
        fecha_fin = tz_bolivia.localize(fecha_fin)

    fecha_inicio = fecha_inicio.replace(tzinfo=None)
    fecha_fin    = fecha_fin.replace(tzinfo=None)

    password_hash = None
    if not form.es_publico.data:
        pwd = form.password.data or ''
        password_hash = generate_password_hash(pwd)

    concurso = Concurso(
        nombre        = form.nombre.data,
        descripcion   = form.descripcion.data,
        fecha_inicio  = fecha_inicio,
        fecha_fin     = fecha_fin,
        es_publico    = form.es_publico.data,
        creado_por    = autor_id,
        password_hash = password_hash,
    )
    db.session.add(concurso)
    db.session.commit()


@concursos_bp.route('/lista-concursos')
@login_required
def lista_concursos():
    tz_bolivia = timezone("America/La_Paz")
    ahora = datetime.now(tz_bolivia)

    concursos = Concurso.query.all()

    concursos_activos = []
    concursos_proximos = []
    concursos_finalizados = []

    for c in concursos:
        fecha_inicio = tz_bolivia.localize(c.fecha_inicio) if c.fecha_inicio.tzinfo is None else c.fecha_inicio
        fecha_fin = tz_bolivia.localize(c.fecha_fin) if c.fecha_fin.tzinfo is None else c.fecha_fin

        if fecha_inicio > ahora:
            concursos_proximos.append(c)
        elif fecha_inicio <= ahora <= fecha_fin:
            concursos_activos.append(c)
        else:
            concursos_finalizados.append(c)

    return render_template(
        'concursos/lista.html',
        concursos_activos=concursos_activos,
        concursos_proximos=concursos_proximos,
        concursos_finalizados=concursos_finalizados,
        timedelta=timedelta
    )

@concursos_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_concurso(id):
    if not current_user.es_admin:
        flash('No tienes permiso para esta acción.', 'danger')
        return redirect(url_for('concursos.lista_concursos'))

    concurso = Concurso.query.get_or_404(id)

    #from pytz import timezone
    #from datetime import datetime
    tz_bolivia = timezone("America/La_Paz")
    ahora = datetime.now(tz_bolivia).replace(tzinfo=None)

    problemas_actuales_ids = [cp.problema_id for cp in concurso.concursos_problemas]

    problemas_ocupados_subq = db.session.query(ConcursoProblema.problema_id).join(
        Concurso, ConcursoProblema.concurso_id == Concurso.id
    ).filter(
        Concurso.fecha_fin > ahora,
        Concurso.id != concurso.id
    ).subquery()

    q_publicos = request.args.get('q_publicos', '', type=str)
    q_privados = request.args.get('q_privados', '', type=str)

    page_publicos = request.args.get('page_publicos', 1, type=int)
    page_privados = request.args.get('page_privados', 1, type=int)

    problemas_publicos_query = Problema.query.filter(
        Problema.es_publico == True,
        or_(
            ~Problema.id.in_(problemas_ocupados_subq),
            Problema.id.in_(problemas_actuales_ids)
        )
    )
    if q_publicos:
        problemas_publicos_query = problemas_publicos_query.filter(
            (Problema.codigo.ilike(f"%{q_publicos}%")) |
            (Problema.titulo.ilike(f"%{q_publicos}%"))
        )
    problemas_publicos = problemas_publicos_query.order_by(Problema.codigo).paginate(page=page_publicos, per_page=10)

    problemas_privados_query = Problema.query.filter(
        Problema.autor_id == current_user.id,
        Problema.es_publico == False,
        or_(
            ~Problema.id.in_(problemas_ocupados_subq),
            Problema.id.in_(problemas_actuales_ids)
        )
    )
    if q_privados:
        problemas_privados_query = problemas_privados_query.filter(
            (Problema.codigo.ilike(f"%{q_privados}%")) |
            (Problema.titulo.ilike(f"%{q_privados}%"))
        )
    problemas_privados = problemas_privados_query.order_by(Problema.codigo).paginate(page=page_privados, per_page=10)

    if request.method == 'POST':
        problemas_seleccionados_ids = request.form.getlist('problemas')
        ConcursoProblema.query.filter_by(concurso_id=concurso.id).delete()
        for orden, problema_id in enumerate(problemas_seleccionados_ids, start=1):
            db.session.add(ConcursoProblema(concurso_id=concurso.id, problema_id=int(problema_id), orden_problema=orden))
        db.session.commit()
        flash('Problemas actualizados correctamente.', 'success')
        return redirect(url_for('concursos.lista_concursos', id=concurso.id))

    return render_template(
        'concursos/editar.html',
        concurso=concurso,
        problemas_publicos=problemas_publicos,
        problemas_privados=problemas_privados,
        problemas_actuales_ids=problemas_actuales_ids
    )

@concursos_bp.route('/<int:id>/ver', methods=['GET'])
@login_required
def ver_concurso(id):
    concurso = Concurso.query.get_or_404(id)
    if not concurso.es_publico:
        tiene_acceso = (
            current_user.es_admin or 
            current_user.id == concurso.creado_por or 
            session.get(f'acceso_concurso_{concurso.id}', False)
        )
        if not tiene_acceso:
            flash('Este concurso es privado. Necesitas ingresar la contraseña.', 'warning')
            return redirect(url_for('concursos.verificar_password', concurso_id=id))

    zona_bolivia = timezone("America/La_Paz")
    now = datetime.now(zona_bolivia).replace(tzinfo=None)
    if concurso.fecha_inicio and now < concurso.fecha_inicio:
        if not (current_user.es_admin or current_user.id == concurso.creado_por):
            flash('Este concurso aún no ha iniciado.', 'warning')
            return redirect(url_for('concursos.lista_concursos'))

    veredictos = {}
    for cp in concurso.concursos_problemas:
        envios = (
            Envio.query
            .filter_by(usuario_id=current_user.id,
                       concurso_id=concurso.id,
                       problema_id=cp.problema_id)
            .order_by(Envio.enviado_en.asc())
            .all()
        )

        intentos = 0
        resuelto = False
        for envio in envios:
            intentos += 1
            if envio.veredicto and envio.veredicto.codigo == 'AC':
                resuelto = True
                break
        if envios:
            veredictos[cp.problema_id] = {
                'resuelto': resuelto,
                'intentos': intentos,
                'color': random.randint(0, 6)
            }

    envios_usuario = (
        Envio.query
        .filter_by(usuario_id=current_user.id,
                   concurso_id=concurso.id)
        .order_by(Envio.enviado_en.desc())
        .limit(10)
        .all()
    )

    problemas = [cp.problema for cp in concurso.concursos_problemas]

    return render_template(
        'concursos/ver_concurso.html',
        concurso=concurso,
        now=now,
        veredictos=veredictos,
        envios_usuario=envios_usuario,
        problemas=problemas
    )

@concursos_bp.route('/<int:concurso_id>/problema/<int:problema_id>', endpoint='ver_problema_publico')
@login_required
def ver_problema_publico(concurso_id, problema_id):

    concurso = Concurso.query.get_or_404(concurso_id)
    problema = Problema.query.get_or_404(problema_id)

    enlace = ConcursoProblema.query.filter_by(
        concurso_id=concurso_id,
        problema_id=problema_id
    ).first()
    if not enlace:
        flash("Este problema no pertenece a ese concurso.", "danger")
        return redirect(url_for('concursos.lista_concursos'))

    tz_bol = timezone("America/La_Paz")
    now = datetime.now(tz_bol).replace(tzinfo=None)

    fi, ff = concurso.fecha_inicio, concurso.fecha_fin
    inicio = fi if fi.tzinfo else tz_bol.localize(fi).replace(tzinfo=None)
    fin    = ff if ff.tzinfo else tz_bol.localize(ff).replace(tzinfo=None)

    tiene_acceso_privado = session.get(f'acceso_concurso_{concurso.id}', False)

    puede_ver = (
        current_user.es_admin or
        current_user.id == problema.autor_id or
        (concurso.es_publico and inicio <= now <= fin) or
        (not concurso.es_publico and tiene_acceso_privado and inicio <= now <= fin)
    )
    if not puede_ver:
        flash(
            f"Este problema solo está disponible entre "
            f"{inicio.strftime('%Y-%m-%d %H:%M')} y {fin.strftime('%Y-%m-%d %H:%M')}. "
            f"Ahora son {now.strftime('%Y-%m-%d %H:%M')}.",
            "danger"
        )
        return redirect(url_for('concursos.lista_concursos'))

    envios = (Envio.query
              .filter_by(problema_id=problema_id, concurso_id=concurso_id)
              .order_by(Envio.enviado_en.desc())
              .limit(10)
              .all())
    total_envios = Envio.query.filter_by(problema_id=problema_id, concurso_id=concurso_id).count()
    aceptados = (Envio.query
                 .join(Veredicto)
                 .filter(
                     Envio.problema_id == problema_id,
                     Envio.concurso_id == concurso_id,
                     Veredicto.codigo == 'AC'
                 ).count())
    rechazados = total_envios - aceptados
    lenguajes = Lenguaje.query.all()

    return render_template(
        'concursos/ver_problema.html',
        concurso=concurso,
        problema=problema,
        envios=envios,
        total_envios=total_envios,
        aceptados=aceptados,
        rechazados=rechazados,
        lenguajes=lenguajes,
        now=now
    )

@concursos_bp.route('/<int:concurso_id>/enviar/<int:problema_id>', methods=['POST'])
@login_required
def enviar(concurso_id, problema_id):
    problema = Problema.query.get_or_404(problema_id)
    lenguaje_id = request.form.get('lenguaje_id')
    archivo = request.files.get('archivo')
    lenguaje = Lenguaje.query.get_or_404(lenguaje_id)

    ahora_local = datetime.now(timezone("America/La_Paz"))
    ahora_utc = ahora_local.astimezone(timezone("UTC")).replace(tzinfo=None)

    concurso_problema = ConcursoProblema.query.filter_by(
        concurso_id=concurso_id,
        problema_id=problema_id
    ).first()

    if concurso_problema is None:
        flash('El problema no pertenece a este concurso.', 'danger')
        return redirect(url_for('concursos.ver_concurso', id=concurso_id))

    if not archivo:
        flash('Debes subir un archivo.', 'danger')
        return redirect(url_for('concursos.ver_problema_publico', problema_id=problema.id))


    zona_bolivia = timezone("America/La_Paz")
    now = datetime.now(zona_bolivia).replace(tzinfo=None)

    try:
        nuevo_envio = Envio(
            usuario_id=current_user.id,
            problema_id=problema.id,
            concurso_id=concurso_id, 
            lenguaje_id=lenguaje.id,
            codigo_fuente='',
            veredicto_id=None,
            tiempo_ejecucion=None,
            memoria_usada=None,
            enviado_en=now
        )
        db.session.add(nuevo_envio)
        db.session.commit()

        base_dir = os.path.join('app', 'data_problemas', problema.codigo, f'envio_{nuevo_envio.id}')
        os.makedirs(base_dir, exist_ok=True)

        nombre_archivo = f"main{lenguaje.extension_archivo}"
        ruta_completa = os.path.join(base_dir, nombre_archivo)

        archivo.save(ruta_completa)

        with open(ruta_completa, 'r', encoding='utf-8') as f:
            codigo_fuente = f.read()

        nuevo_envio.codigo_fuente = codigo_fuente
        db.session.commit()

        if not codigo_fuente.strip():
            flash('El archivo está vacío o no se pudo leer.', 'danger')
            return redirect(url_for('concursos.ver_problema_publico', problema_id=problema.id))

        if not os.path.isfile(ruta_completa):
            flash('No se pudo guardar el archivo.', 'danger')
            return redirect(url_for('concursos.ver_problema_publico', problema_id=problema.id))

        cola_envios.put(nuevo_envio.id)

        flash('Envío guardado correctamente. Será evaluado pronto.', 'success')
        return redirect(url_for('concursos.ver_concurso', id=concurso_id))

    except Exception as e:
        flash(f'Error al procesar el envío: {e}', 'danger')
        return redirect(url_for('concursos.ver_problema_publico', problema_id=problema.id))

@concursos_bp.route('/editar/<int:concurso_id>', methods=['GET', 'POST'])
@login_required
def editar_concurso_update(concurso_id):
    zona_bolivia = timezone("America/La_Paz")
    ahora = datetime.now(zona_bolivia)

    concurso = Concurso.query.get_or_404(concurso_id)

    if not current_user.es_admin:
        flash('Acceso denegado. Solo los administradores pueden editar concursos.', 'danger')
        return redirect(url_for('main.dashboard'))

    form = ConcursoForm(obj=concurso)

    if form.validate_on_submit():
        form.populate_obj(concurso) 

        if form.es_publico.data:
            concurso.password_hash = None
        else:
            if form.password.data and form.password.data.strip():
                concurso.password_hash = generate_password_hash(form.password.data)

        db.session.commit()
        flash('Concurso actualizado correctamente.', 'success')
        return redirect(url_for('concursos.lista_concursos', concurso_id=concurso.id))

    return render_template('concursos/editar_update.html', form=form, concurso=concurso)

@concursos_bp.route('/acceso_privado/<int:concurso_id>', methods=['GET', 'POST'])
@login_required
def acceso_privado(concurso_id):
    concurso = Concurso.query.get_or_404(concurso_id)
    form = PasswordForm()
    error = False

    if form.validate_on_submit():
        if check_password_hash(concurso.password_hash, form.password.data):
            session[f'acceso_concurso_{concurso.id}'] = True
            return redirect(url_for('concursos.ver_concurso', id=concurso.id))
        else:
            error = True

    zona_bolivia = timezone("America/La_Paz")
    now = datetime.now(zona_bolivia).replace(tzinfo=None)

    return render_template(
        'concursos/acceso_privado.html',
        form=form,
        concurso=concurso,
        now=now,
        error=error
    )

class PasswordForm(FlaskForm):
    password = PasswordField('Contraseña', validators=[DataRequired()])
    submit = SubmitField('Acceder')


@concursos_bp.route('/concursos/<int:concurso_id>/ranking')
def ranking(concurso_id):
    page = request.args.get('page', 1, type=int)
    per_page = 10

    concurso = Concurso.query.get_or_404(concurso_id)
    inicio_concurso = concurso.fecha_inicio
    problemas = (
        db.session.query(Problema)
        .join(ConcursoProblema, ConcursoProblema.problema_id == Problema.id)
        .filter(ConcursoProblema.concurso_id == concurso_id)
        .order_by(ConcursoProblema.orden_problema.asc())
        .all()
    )

    participantes = (
        db.session.query(Usuario)
        .join(Envio, Envio.usuario_id == Usuario.id)
        .filter(Envio.concurso_id == concurso_id)
        .distinct()
        .all()
    )

    envios = (
        db.session.query(
            Envio.usuario_id,
            Envio.problema_id,
            Envio.enviado_en,
            Veredicto.codigo
        )
        .join(Veredicto, Envio.veredicto_id == Veredicto.id)
        .filter(Envio.concurso_id == concurso_id)
        .order_by(Envio.enviado_en.asc())
        .all()
    )
    envio_map = defaultdict(list)
    for e in envios:
        envio_map[(e.usuario_id, e.problema_id)].append(e)

    ranking = []
    for pos, participante in enumerate(participantes, start=1 + (page - 1) * per_page):
        resueltos = 0
        total_envios = 0
        total_tiempo = 0
        ultimo_envio = None
        detalle_problemas = {}

        for problema in problemas:
            clave = (participante.id, problema.id)
            envs = envio_map.get(clave, [])
            intentos = 0
            resuelto = False
            tiempo_resolucion = None

            for e in envs:
                intentos += 1
                if not ultimo_envio or e.enviado_en > ultimo_envio:
                    ultimo_envio = e.enviado_en
                if e.codigo == 'AC':
                    resuelto = True
                    tiempo_resolucion = (e.enviado_en - inicio_concurso).total_seconds() // 60
                    break

            if resuelto:
                resueltos += 1
                penalizacion = (intentos - 1) * 20
                total_tiempo += tiempo_resolucion + penalizacion
                detalle_problemas[problema.id] = f"+{intentos}"
            elif intentos > 0:
                detalle_problemas[problema.id] = f"-{intentos}"
            else:
                detalle_problemas[problema.id] = "--"

            total_envios += intentos

        ranking.append({
            'pos': pos,
            'nombre_usuario': participante.nombre_usuario,
            'detalle_problemas': detalle_problemas,
            'resueltos': resueltos,
            'ultimo_envio': ultimo_envio.strftime('%H:%M:%S') if ultimo_envio else '-',
            'total_ac': resueltos,
            'tiempo_total': int(total_tiempo)
        })

    ranking.sort(key=lambda u: (-u['resueltos'], u['tiempo_total']))

    total = len(ranking)
    pages = (total + per_page - 1) // per_page
    ranking_pag = ranking[(page - 1) * per_page: page * per_page]

    letras_problemas = {
        problema.id: {
            'codigo': problema.codigo,
            'titulo': problema.titulo
        }
        for problema in problemas
    }


    return render_template(
        'concursos/ranking.html',
        ranking=ranking_pag,
        page=page,
        pages=pages,
        concurso_id=concurso_id,
        letras_problemas=letras_problemas,
        problemas=problemas
    )

@concursos_bp.route('/concursos/eliminar/<int:concurso_id>', methods=['POST'])
@login_required
def eliminar_concurso(concurso_id):
    concurso = Concurso.query.get_or_404(concurso_id)

    # Verificar que el usuario sea el creador o administrador
    if concurso.creado_por != current_user.id and not current_user.es_admin:
        abort(403)

    # Aquí puedes agregar lógica para eliminar archivos o datos relacionados si los tienes

    try:
        db.session.delete(concurso)
        db.session.commit()
        flash('Concurso eliminado exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error al eliminar el concurso.', 'danger')

    return redirect(url_for('concursos.lista_concursos'))

def ahora_utc():
    return datetime.now(timezone("America/La_Paz")).replace(tzinfo=None)

def utc_a_bolivia(fecha_utc):
    tz_bolivia = timezone("America/La_Paz")
    fecha_utc = fecha_utc.replace(tzinfo=timezone("UTC"))
    return fecha_utc.astimezone(tz_bolivia).strftime("%Y-%m-%d %H:%M")

def localiza_bolivia(fecha_naive):
    tz_bolivia = timezone("America/La_Paz")
    if fecha_naive.tzinfo is None:
        return tz_bolivia.localize(fecha_naive)
    return fecha_naive


