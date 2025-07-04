from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField, BooleanField, SubmitField, PasswordField, DateTimeField
from wtforms.validators import DataRequired, NumberRange, EqualTo, Email, Length, Optional

from wtforms import Form, validators


from wtforms import ValidationError


class LoginForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired(), Length(min=3, max=50)])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    submit = SubmitField('Entrar')

class RegisterForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired(), Length(min=3, max=50)])
    email = StringField('Correo electrónico', validators=[DataRequired(), Email(), Length(max=100)])
    password = PasswordField('Contraseña', validators=[DataRequired(), Length(min=5)])
    confirm_password = PasswordField('Confirmar Contraseña', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Registrarse')

class ProblemaForm(FlaskForm):
    codigo = StringField('Código', validators=[DataRequired(), Length(max=20)])
    titulo = StringField('Título', validators=[DataRequired(), Length(max=100)])
    descripcion = TextAreaField('Descripción')
    descripcion_entrada = TextAreaField('Descripción de la entrada')
    descripcion_salida = TextAreaField('Descripción de la salida')
    limite_tiempo = IntegerField('Límite de tiempo (segundos)', validators=[DataRequired(), NumberRange(min=1, max=10)])
    limite_memoria = IntegerField('Límite de memoria (MB)', validators=[DataRequired(), NumberRange(min=1, max=512)])
    entrada_ejemplo = TextAreaField('Entrada de ejemplo')
    salida_ejemplo = TextAreaField('Salida de ejemplo')
    es_publico = BooleanField('¿Es público?')
    submit = SubmitField('Registrar')


class ConcursoForm(FlaskForm):
    nombre        = StringField('Nombre', validators=[DataRequired()])
    descripcion   = TextAreaField('Descripción', validators=[Optional()])
    fecha_inicio  = DateTimeField('Fecha de inicio', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    fecha_fin     = DateTimeField('Fecha de fin', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    es_publico    = BooleanField('¿Es público?')
    password      = PasswordField('Contraseña', validators=[Optional()])  # no obligatoria a nivel de campo

    def validate(self, extra_validators=None):
        if not super().validate(extra_validators=extra_validators):
            return False

        if not self.es_publico.data:
            if not self.password.data or not self.password.data.strip():
                self.password.errors.append("Debe ingresar una contraseña para concursos privados.")
                return False

        return True
 
 
class UsuarioForm(FlaskForm):
    nombre_usuario = StringField('Nombre de Usuario', validators=[DataRequired()])
    correo = StringField('Correo', validators=[DataRequired(), Email()])
    rol_id = IntegerField('Rol ID', validators=[DataRequired()])
    submit = SubmitField('Guardar')

class EditarProblemaFormAdmin(FlaskForm):
    codigo = StringField('Código', validators=[DataRequired()])
    titulo = StringField('Título', validators=[DataRequired()])
    descripcion = TextAreaField('Descripción', validators=[Optional()])
    descripcion_entrada = TextAreaField('Descripción de Entrada', validators=[Optional()])
    descripcion_salida = TextAreaField('Descripción de Salida', validators=[Optional()])
    limite_tiempo = IntegerField('Límite de Tiempo (ms)', validators=[Optional()])
    limite_memoria = IntegerField('Límite de Memoria (MB)', validators=[Optional()])
    entrada_ejemplo = TextAreaField('Entrada de Ejemplo', validators=[Optional()])
    salida_ejemplo = TextAreaField('Salida de Ejemplo', validators=[Optional()])
    es_publico = BooleanField('Es Público')