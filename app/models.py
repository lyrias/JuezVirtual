from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db



class Rol(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)

    usuarios = db.relationship('Usuario', backref='rol', lazy=True)

    def __repr__(self):
        return f'<Rol {self.nombre}>'

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    nombre_usuario = db.Column(db.String(50), unique=True, nullable=False)
    correo = db.Column(db.String(100), unique=True, nullable=False)
    contrasena_hash = db.Column(db.String(200), nullable=False)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    rol_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)


    concursos_creados = db.relationship('Concurso', back_populates='creador', lazy=True)
    envios = db.relationship('Envio', back_populates='usuario', lazy=True)
    problemas_creados = db.relationship('Problema', backref='autor', lazy=True)

    inscripciones = db.relationship('Inscripcion', back_populates='usuario')
    concursos = db.relationship('Concurso', secondary='inscripciones', back_populates='usuarios')
    activo = db.Column(db.Boolean, default=True, nullable=False)
    
    @property
    def es_admin(self):
        return self.rol_id == 1

    def __repr__(self):
        return f'<Usuario {self.nombre_usuario}>'

class Concurso(db.Model):
    __tablename__ = 'concursos'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    fecha_inicio = db.Column(db.DateTime)
    fecha_fin = db.Column(db.DateTime)
    es_publico = db.Column(db.Boolean, default=True)
    creado_por = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    password_hash = db.Column(db.String(255), nullable=True)

    creador = db.relationship('Usuario', back_populates='concursos_creados')

    inscripciones = db.relationship('Inscripcion', back_populates='concurso')
    usuarios = db.relationship('Usuario', secondary='inscripciones', back_populates='concursos')

    concursos_problemas = db.relationship(
        'ConcursoProblema',
        back_populates='concurso',
        cascade='all, delete',
        passive_deletes=True
    )

    problemas = db.relationship(
        'Problema',
        secondary='concursos_problemas',
        back_populates='concursos',
        viewonly=True
    )

    def obtener_envios(self):
        from app.models import Envio, ConcursoProblema, Problema
        return Envio.query.join(Problema).join(ConcursoProblema).filter(
            ConcursoProblema.concurso_id == self.id
        ).all()

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

class Problema(db.Model):
    __tablename__ = 'problemas'

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), unique=True, nullable=False)
    titulo = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    descripcion_entrada = db.Column(db.Text)
    descripcion_salida = db.Column(db.Text)
    limite_tiempo = db.Column(db.Integer)  
    limite_memoria = db.Column(db.Integer)  
    entrada_ejemplo = db.Column(db.Text)
    salida_ejemplo = db.Column(db.Text)

    autor_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    es_publico = db.Column(db.Boolean, default=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    casos_prueba = db.relationship('CasoPrueba', back_populates='problema', lazy=True)
    envios = db.relationship('Envio', back_populates='problema', lazy=True)

    concursos_problemas = db.relationship(
        'ConcursoProblema',
        back_populates='problema',
        cascade='all, delete-orphan'
    )

    concursos = db.relationship(
        'Concurso',
        secondary='concursos_problemas',
        back_populates='problemas',
        viewonly=True
    )

    def __repr__(self):
        return f'<Problema {self.codigo}>'

class CasoPrueba(db.Model):
    __tablename__ = 'casos_prueba'

    id = db.Column(db.Integer, primary_key=True)
    problema_id = db.Column(db.Integer, db.ForeignKey('problemas.id'), nullable=False)
    entrada = db.Column(db.Text)
    salida_esperada = db.Column(db.Text)
    es_publico = db.Column(db.Boolean, default=False)

    problema = db.relationship('Problema', back_populates='casos_prueba')

    def __repr__(self):
        return f'<CasoPrueba {self.id} de Problema {self.problema_id}>'

class Lenguaje(db.Model):
    __tablename__ = 'lenguajes'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    comando_compilar = db.Column(db.Text)
    extension_archivo = db.Column(db.String(10))

    envios = db.relationship('Envio', back_populates='lenguaje', lazy=True)

    def __repr__(self):
        return f'<Lenguaje {self.nombre}>'

class Veredicto(db.Model):
    __tablename__ = 'veredictos'

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), nullable=False) 
    descripcion = db.Column(db.String(100))

    envios = db.relationship('Envio', back_populates='veredicto', lazy=True)

    def __repr__(self):
        return f'<Veredicto {self.codigo}>'

class ConcursoProblema(db.Model):
    __tablename__ = 'concursos_problemas'

    id = db.Column(db.Integer, primary_key=True)
    concurso_id = db.Column(db.Integer, db.ForeignKey('concursos.id', ondelete='CASCADE'), nullable=False)
    problema_id = db.Column(db.Integer, db.ForeignKey('problemas.id', ondelete='CASCADE'), nullable=False)
    orden_problema = db.Column(db.Integer)

    concurso = db.relationship('Concurso', back_populates='concursos_problemas')
    problema = db.relationship('Problema', back_populates='concursos_problemas')

    def __repr__(self):
        return f'<ConcursoProblema C{self.concurso_id}-P{self.problema_id}>'

class Envio(db.Model):
    __tablename__ = 'envios'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    problema_id = db.Column(db.Integer, db.ForeignKey('problemas.id'), nullable=False)
    concurso_id = db.Column(db.Integer, db.ForeignKey('concursos.id'), nullable=True)
    lenguaje_id = db.Column(db.Integer, db.ForeignKey('lenguajes.id'), nullable=False)
    codigo_fuente = db.Column(db.Text, nullable=False)
    veredicto_id = db.Column(db.Integer, db.ForeignKey('veredictos.id'), nullable=True)
    tiempo_ejecucion = db.Column(db.Float)
    memoria_usada = db.Column(db.Integer)
    enviado_en = db.Column(db.DateTime, default=datetime.utcnow)

    usuario = db.relationship('Usuario', back_populates='envios')
    problema = db.relationship('Problema', back_populates='envios')
    concurso = db.relationship('Concurso') 
    lenguaje = db.relationship('Lenguaje', back_populates='envios')
    veredicto = db.relationship('Veredicto', back_populates='envios')

    def __repr__(self):
        return f'<Envio #{self.id} Usuario:{self.usuario_id} Problema:{self.problema_id}>'

class Inscripcion(db.Model):
    __tablename__ = 'inscripciones'
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), primary_key=True)
    concurso_id = db.Column(db.Integer, db.ForeignKey('concursos.id'), primary_key=True)
    fecha_inscripcion = db.Column(db.DateTime, default=datetime.utcnow)

    usuario = db.relationship('Usuario', back_populates='inscripciones')
    concurso = db.relationship('Concurso', back_populates='inscripciones')
