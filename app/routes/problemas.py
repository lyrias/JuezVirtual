from flask import abort, Blueprint, render_template, redirect, url_for, flash, request, current_app, Response
from flask_login import login_required, current_user
from app import db
from app.forms import ProblemaForm
from app.models import Problema, Envio, Veredicto, Usuario, Lenguaje
from sqlalchemy import func, case
from app.forms import EditarProblemaFormAdmin

import os
from werkzeug.utils import secure_filename

from datetime import datetime

from app.cola_envios import cola_envios



problemas_bp = Blueprint('problemas', __name__, url_prefix='/problemas')

@problemas_bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_problema():
    if not current_user.es_admin:
        flash('Acceso denegado.', 'danger')
        return redirect(url_for('main.dashboard'))

    form = ProblemaForm()
    if form.validate_on_submit():
        existe = Problema.query.filter_by(codigo=form.codigo.data).first()
        if existe:
            flash('El código ya está registrado. Por favor elige otro.', 'danger')
            return render_template('admin/nuevo_problema.html', form=form)

        nuevo = Problema(
            codigo=form.codigo.data,
            titulo=form.titulo.data,
            descripcion=form.descripcion.data,
            descripcion_entrada=form.descripcion_entrada.data,
            descripcion_salida=form.descripcion_salida.data,
            limite_tiempo=form.limite_tiempo.data,
            limite_memoria=form.limite_memoria.data,
            entrada_ejemplo=form.entrada_ejemplo.data,
            salida_ejemplo=form.salida_ejemplo.data,
            es_publico=form.es_publico.data,
            autor_id=current_user.id
        )
        db.session.add(nuevo)
        db.session.commit()
        
        carpeta_base = os.path.join(current_app.root_path, 'data_problemas')
        os.makedirs(carpeta_base, exist_ok=True)

        ruta_problema = os.path.join(carpeta_base, nuevo.codigo)
        os.makedirs(ruta_problema, exist_ok=True)

        archivo_entradas = request.files.get('archivo_entradas')
        archivo_salidas = request.files.get('archivo_salidas')

        if archivo_entradas and archivo_salidas:
            if not es_archivo_txt(archivo_entradas.filename):
                flash('El archivo de entradas debe tener extensión .txt', 'warning')
                return render_template('admin/nuevo_problema.html', form=form)
            if not es_archivo_txt(archivo_salidas.filename):
                flash('El archivo de salidas debe tener extensión .txt', 'warning')
                return render_template('admin/nuevo_problema.html', form=form)

            nombre_entrada = secure_filename('entradas.txt')
            nombre_salida = secure_filename('salidas.txt')

            archivo_entradas.save(os.path.join(ruta_problema, nombre_entrada))
            archivo_salidas.save(os.path.join(ruta_problema, nombre_salida))
        else:
            flash('No se subieron los archivos de entrada y salida correctamente.', 'warning')
            return render_template('admin/nuevo_problema.html', form=form)

        flash('Problema registrado correctamente.', 'success')
        return redirect(url_for('problemas.nuevo_problema'))

    return render_template('admin/nuevo_problema.html', form=form)

@problemas_bp.route('/mis-problemas')
@login_required
def mis_problemas():
    datos = (
        db.session.query(
            Problema,
            func.count(Envio.id).label('total_envios'),
            func.sum(case((Veredicto.codigo == 'AC', 1), else_=0)).label('total_aceptados'),
            func.sum(case((Veredicto.codigo != 'AC', 1), else_=0)).label('total_errores')
        )
        .outerjoin(Envio, Envio.problema_id == Problema.id)
        .outerjoin(Veredicto, Veredicto.id == Envio.veredicto_id)
        .filter(Problema.autor_id == current_user.id)
        .group_by(Problema.id)
        .all()
    )

    return render_template('admin/mis_problemas.html', datos_problemas=datos)

@problemas_bp.route('/editar/<int:problema_id>', methods=['GET', 'POST'])
@login_required
def editar_problema(problema_id):
    problema = Problema.query.get_or_404(problema_id)

    if problema.autor_id != current_user.id:
        flash("No tienes permiso para editar este problema.", "danger")
        return redirect(url_for('problemas.mis_problemas'))

    form = ProblemaForm(obj=problema)

    if form.validate_on_submit():
        form.populate_obj(problema)
        db.session.commit()
        
        carpeta_base = os.path.join(current_app.root_path, 'data_problemas')
        ruta_problema = os.path.join(carpeta_base, problema.codigo)
        os.makedirs(ruta_problema, exist_ok=True)

        archivo_entradas = request.files.get('archivo_entradas')
        archivo_salidas = request.files.get('archivo_salidas')

        if archivo_entradas and archivo_entradas.filename != '':
            if es_archivo_txt(archivo_entradas.filename):
                nombre_entrada = secure_filename('entradas.txt')
                archivo_entradas.save(os.path.join(ruta_problema, nombre_entrada))
            else:
                flash('El archivo de entradas debe tener extensión .txt', 'warning')
                return render_template('admin/editar_problema.html', form=form, problema=problema)

        if archivo_salidas and archivo_salidas.filename != '':
            if es_archivo_txt(archivo_salidas.filename):
                nombre_salida = secure_filename('salidas.txt')
                archivo_salidas.save(os.path.join(ruta_problema, nombre_salida))
            else:
                flash('El archivo de salidas debe tener extensión .txt', 'warning')
                return render_template('admin/editar_problema.html', form=form, problema=problema)

        flash("Problema actualizado correctamente.", "success")
        return redirect(url_for('problemas.mis_problemas'))

    return render_template('admin/editar_problema.html', form=form, problema=problema)

@problemas_bp.route('/<int:problema_id>/ver')
@login_required
def ver_problema(problema_id):
    problema = Problema.query.get_or_404(problema_id)

    if not current_user.es_admin and problema.autor_id != current_user.id:
        flash("Acceso denegado", "danger")
        return redirect(url_for('problemas.mis_problemas'))

    envios = Envio.query.filter_by(problema_id=problema_id).order_by(Envio.enviado_en.desc()).limit(10).all()

    total_envios = Envio.query.filter_by(problema_id=problema_id).count()
    aceptados = Envio.query.join(Veredicto).filter(
        Envio.problema_id == problema_id,
        Veredicto.codigo == 'AC'
    ).count()
    rechazados = total_envios - aceptados
    lenguajes = Lenguaje.query.all()
    return render_template('admin/ver_problema.html',
                           problema=problema,
                           envios=envios,
                           total_envios=total_envios,
                           aceptados=aceptados,
                           rechazados=rechazados,
                           lenguajes=lenguajes)

@problemas_bp.route('/listar-problemas')
@login_required
def lista_problemas():
    from app.models import Concurso, ConcursoProblema
    page = request.args.get('page', 1, type=int)
    per_page = 20

    from pytz import timezone
    from datetime import datetime
    tz_bolivia = timezone("America/La_Paz")
    ahora = datetime.now(tz_bolivia).replace(tzinfo=None)

    problemas_ocupados_subq = db.session.query(ConcursoProblema.problema_id).join(
        Concurso, ConcursoProblema.concurso_id == Concurso.id
    ).filter(
        Concurso.fecha_fin > ahora,
    ).subquery()

    subquery = (
        db.session.query(
            Problema.id.label('id'),
            Problema.codigo,
            Problema.titulo,
            Usuario.nombre_usuario.label('autor_nombre'),
            func.count(Envio.id).label('enviados'),
            func.sum(case((Envio.veredicto_id == 1, 1), else_=0)).label('resueltos')
        )
        .join(Usuario, Usuario.id == Problema.autor_id)
        .outerjoin(Envio, Envio.problema_id == Problema.id)
        .filter(
            Problema.es_publico == True,
            ~Problema.id.in_(problemas_ocupados_subq) 
        )
        .group_by(Problema.id, Usuario.nombre_usuario)
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    total = db.session.query(Problema).filter(
        Problema.es_publico == True,
        ~Problema.id.in_(problemas_ocupados_subq)
    ).count()

    return render_template(
        'problemas/lista.html',
        problemas=subquery,
        page=page,
        total=total,
        per_page=per_page
    )


@problemas_bp.route('/publico/<int:problema_id>')
@login_required  
def ver_problema_publico(problema_id):
    problema = Problema.query.get(problema_id)
    if not problema:
        abort(404)  

    if not problema.es_publico:
        return render_template('error/error_privado.html', mensaje="Este problema es privado."), 403

    total_envios = db.session.query(Envio).filter_by(problema_id=problema.id).count()
    aceptados = db.session.query(Envio).filter_by(problema_id=problema.id).filter(Envio.veredicto.has(codigo='AC')).count()
    rechazados = total_envios - aceptados
    
    envios = (
        Envio.query
        .filter_by(problema_id=problema.id)
        .order_by(Envio.enviado_en.desc())
        .limit(10)
        .all()
    )
    
    lenguajes = Lenguaje.query.all()
    return render_template('problemas/ver_problema.html',
                           problema=problema,
                           total_envios=total_envios,
                           aceptados=aceptados,
                           rechazados=rechazados,
                           envios=envios,
                           lenguajes=lenguajes)



@problemas_bp.route('/enviar/<int:problema_id>', methods=['POST'])
@login_required
def enviar(problema_id):
    problema = Problema.query.get_or_404(problema_id)
    lenguaje_id = request.form.get('lenguaje_id')
    archivo = request.files.get('archivo')

    lenguaje = Lenguaje.query.get_or_404(lenguaje_id)

    if not archivo:
        flash('Debes subir un archivo.', 'danger')
        return redirect(url_for('problemas.ver_problema_publico', problema_id=problema_id))

    try:

        nuevo_envio = Envio(
            usuario_id=current_user.id,
            problema_id=problema.id,
            concurso_id=None,
            lenguaje_id=lenguaje.id,
            codigo_fuente='',  
            veredicto_id=None,
            tiempo_ejecucion=None,
            memoria_usada=None,
            enviado_en=datetime.now()
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
            return redirect(url_for('problemas.ver_problema_publico', problema_id=problema.id))

        if not os.path.isfile(ruta_completa):
            flash('No se pudo guardar el archivo.', 'danger')
            return redirect(url_for('problemas.ver_problema_publico', problema_id=problema.id))

        cola_envios.put(nuevo_envio.id) 

        flash('Envío guardado correctamente. Será evaluado pronto.', 'success')
        return redirect(url_for('problemas.ver_problema_publico', problema_id=problema.id))

    except Exception as e:
        flash(f'Error al procesar el envío: {e}', 'danger')
        return redirect(url_for('problemas.ver_problema_publico', problema_id=problema.id))

@problemas_bp.route('/mis-envios')
@login_required
def mis_envios():
    page = request.args.get('page', 1, type=int)
    per_page = 10

    pagination = Envio.query.filter_by(usuario_id=current_user.id) \
                    .order_by(Envio.enviado_en.desc()) \
                    .paginate(page=page, per_page=per_page, error_out=False)
    
    envios = pagination.items
    total = pagination.total

    return render_template('envios/mis_envios.html', envios=envios, page=page, per_page=per_page, total=total)


@problemas_bp.route('/descargar-codigo/<int:envio_id>')
@login_required
def descargar_codigo(envio_id):
    envio = Envio.query.get_or_404(envio_id)
    if envio.usuario_id != current_user.id:
        abort(403)
    
    codigo = envio.codigo_fuente
    lenguaje = envio.lenguaje  
    ext = lenguaje.extension_archivo if lenguaje and lenguaje.extension_archivo else 'txt'
    ext = ext.lstrip('.')
    nombre_archivo = f'envio_{envio.id}.{ext}'
    
    return Response(
        codigo,
        mimetype='text/plain',
        headers={
            "Content-Disposition": f"attachment;filename={nombre_archivo}"
        }
    )

@problemas_bp.route('/ranking-ac')
@login_required
def ranking_ac():
    page = request.args.get('page', 1, type=int)
    per_page = 10

    query = (
        db.session.query(
            Usuario.id,
            Usuario.nombre_usuario,
            func.sum(case((Veredicto.codigo == 'AC', 1), else_=0)).label('ac_count'),
            func.count(Envio.id).label('total_envios')
        )
        .join(Envio, Envio.usuario_id == Usuario.id)
        .join(Veredicto, Veredicto.id == Envio.veredicto_id)
        .group_by(Usuario.id)
        .order_by(func.sum(case((Veredicto.codigo == 'AC', 1), else_=0)).desc())
    )

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    ranking = pagination.items
    total = pagination.total
    pages = pagination.pages

    return render_template('problemas/ranking.html', ranking=ranking, page=page, pages=pages, total=total)

@problemas_bp.route('/problemas/admin')
@login_required
def ver_problema_admin():
    problemas = Problema.query.filter_by(es_publico=True).all()
    return render_template('problemas/ver_problema_admin.html', problemas=problemas)


@problemas_bp.route('/problemas/editar_admin/<int:problema_id>', methods=['GET', 'POST'])
@login_required
def editar_problema_admin(problema_id):
    if not current_user.es_admin:
        abort(403)

    problema = Problema.query.get_or_404(problema_id)
    form = EditarProblemaFormAdmin(obj=problema)

    if form.validate_on_submit():
        form.populate_obj(problema)
        db.session.commit()

        # Manejar archivos .txt opcionales
        entrada_file = request.files.get('archivo_entradas')
        salida_file = request.files.get('archivo_salidas')
        base_path = os.path.join('data/problemas', problema.codigo)
        os.makedirs(base_path, exist_ok=True)

        if entrada_file and entrada_file.filename.endswith('.txt'):
            entrada_path = os.path.join(base_path, 'entradas.txt')
            entrada_file.save(entrada_path)

        if salida_file and salida_file.filename.endswith('.txt'):
            salida_path = os.path.join(base_path, 'salidas.txt')
            salida_file.save(salida_path)

        flash('Problema actualizado correctamente.', 'success')
        return redirect(url_for('problemas.ver_problema_admin'))

    return render_template('problemas/editar_problema_admin.html', form=form, problema=problema)




def es_archivo_txt(filename):
    return '.' in filename and filename.lower().endswith('.txt')