from flask import Blueprint, render_template
from flask_login import login_required
from app.models import Problema, Concurso, Envio, Usuario, Rol
from app import db
from flask_login import login_required, current_user
from flask import request, redirect, url_for, flash
from datetime import datetime
from pytz import timezone
from werkzeug.security import generate_password_hash
main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/dashboard')
@login_required
def dashboard():
    zona_bolivia = timezone("America/La_Paz")
    now = datetime.now(zona_bolivia).replace(tzinfo=None)

    ultimos_problemas = Problema.query.order_by(Problema.fecha_creacion.desc()).limit(3).all()
    concursos_activos = (
        Concurso.query
        .filter(Concurso.fecha_fin >= now)
        .order_by(Concurso.fecha_inicio.asc())
        .limit(3)
        .all()
    )

    ultimos_envios = (
        Envio.query
        .filter_by(usuario_id=current_user.id)
        .order_by(Envio.enviado_en.desc())
        .limit(5)
        .all()
    )
    return render_template(
        'dashboard.html',
        ultimos_problemas=ultimos_problemas,
        concursos_activos=concursos_activos,
        ultimos_envios=ultimos_envios,
        now=now 
    )

@main.route('/admin/usuarios')
@login_required
def listar_usuarios():
    #usuarios = Usuario.query.all()
    usuarios = Usuario.query.filter_by(activo=True).all()
    return render_template('admin/listar_usuarios.html', usuarios=usuarios)


@main.route("/admin/usuarios/<int:usuario_id>/editar", methods=["GET", "POST"])
@login_required
def editar_usuario(usuario_id):
    # Solo admins pueden editar (opcional)
    if not current_user.es_admin:
        flash('No tienes permiso para editar usuarios.', 'danger')
        return redirect(url_for('main.dashboard'))

    usuario = Usuario.query.get_or_404(usuario_id)
    roles = Rol.query.all()

    if request.method == 'POST':
        usuario.nombre_usuario = request.form['nombre_usuario']
        usuario.correo = request.form['correo']
        usuario.rol_id = int(request.form['rol_id'])

        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')

        if password:
            if password != password_confirm:
                flash('Las contraseñas no coinciden.', 'danger')
                return redirect(url_for('main.editar_usuario', usuario_id=usuario.id))
            usuario.contrasena_hash = generate_password_hash(password)

        db.session.commit()
        flash('Usuario actualizado con éxito.', 'success')
        return redirect(url_for('main.listar_usuarios'))

    return render_template("admin/editar_usuario.html", usuario=usuario, roles=roles)


@main.route("/admin/usuarios/<int:usuario_id>/eliminar", methods=["POST"])
@login_required
def eliminar_usuario(usuario_id):
    usuario = Usuario.query.get_or_404(usuario_id)

    # Evita que un admin se elimine a sí mismo (opcional)
    if current_user.id == usuario.id:
        flash("No puedes eliminar tu propio usuario.", "warning")
        return redirect(url_for('main.listar_usuarios'))

    usuario.activo = False
    db.session.commit()

    flash("Usuario desactivado correctamente.", "success")
    return redirect(url_for('main.listar_usuarios'))

@main.route("/admin/lenguajes/", methods=["POST"])
@login_required
def lista_lenguajes():
    lenguajes = Lenguaje.query.all()
    return render_template('lenguajes/lista.html', lenguajes=lenguajes)