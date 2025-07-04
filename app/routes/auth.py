from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash

from app.models import db, Usuario  
from app.forms import LoginForm, RegisterForm

from sqlalchemy.exc import OperationalError

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        try:
            usuario = Usuario.query.filter_by(nombre_usuario=form.username.data).first()
        except OperationalError:
            return render_template("error/error_conexion.html"), 503

        if usuario and usuario.activo and check_password_hash(usuario.contrasena_hash, form.password.data):
            login_user(usuario)
            flash('Sesión iniciada correctamente.', 'success')
            return redirect(url_for('main.dashboard'))

        flash('Usuario o contraseña incorrectos o cuenta inactiva.', 'danger')

    return render_template('login.html', form=form)



@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        try:
            existe = Usuario.query.filter(
                (Usuario.nombre_usuario == form.username.data) | 
                (Usuario.correo == form.email.data)
            ).first()
        except OperationalError:
            return render_template("error/error_conexion.html"), 503
        if existe:
            flash('El usuario o correo ya existe.', 'danger')
            return render_template('register.html', form=form)

        nuevo_usuario = Usuario(
            nombre_usuario=form.username.data,
            correo=form.email.data,
            contrasena_hash=generate_password_hash(form.password.data),
            rol_id=2  
        )
        db.session.add(nuevo_usuario)
        db.session.commit()

        flash('Registro exitoso. Ya puedes iniciar sesión.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('register.html', form=form)

@auth.route('/logout')
def logout():
    logout_user()
    flash('Has cerrado sesión.', 'info')
    return redirect(url_for('auth.login'))

