-- --------------------------------------------------------
-- Host:                         127.0.0.1
-- Server version:               8.4.3 - MySQL Community Server - GPL
-- Server OS:                    Win64
-- HeidiSQL Version:             12.8.0.6908
-- --------------------------------------------------------

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET NAMES utf8 */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;


-- Dumping database structure for juezdb
CREATE DATABASE IF NOT EXISTS `juezdb` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_spanish_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;
USE `juezdb`;

-- Dumping structure for table juezdb.alembic_version
CREATE TABLE IF NOT EXISTS `alembic_version` (
  `version_num` varchar(32) COLLATE utf8mb4_spanish_ci NOT NULL,
  PRIMARY KEY (`version_num`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_spanish_ci;

-- Dumping data for table juezdb.alembic_version: ~1 rows (approximately)
INSERT INTO `alembic_version` (`version_num`) VALUES
	('89d94c1331fa');

-- Dumping structure for table juezdb.casos_prueba
CREATE TABLE IF NOT EXISTS `casos_prueba` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `problema_id` int unsigned NOT NULL,
  `entrada` text COLLATE utf8mb4_spanish_ci,
  `salida_esperada` text COLLATE utf8mb4_spanish_ci,
  `es_publico` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `problema_id` (`problema_id`),
  CONSTRAINT `fk_casosprueba_problema` FOREIGN KEY (`problema_id`) REFERENCES `problemas` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_spanish_ci;

-- Dumping data for table juezdb.casos_prueba: ~0 rows (approximately)

-- Dumping structure for table juezdb.concursos
CREATE TABLE IF NOT EXISTS `concursos` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_spanish_ci NOT NULL,
  `descripcion` text COLLATE utf8mb4_spanish_ci,
  `fecha_inicio` datetime DEFAULT NULL,
  `fecha_fin` datetime DEFAULT NULL,
  `es_publico` tinyint(1) DEFAULT NULL,
  `creado_por` int unsigned NOT NULL,
  `password_hash` varchar(255) COLLATE utf8mb4_spanish_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `creado_por` (`creado_por`),
  CONSTRAINT `fk_concursos_creado_por` FOREIGN KEY (`creado_por`) REFERENCES `usuarios` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=41 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_spanish_ci;

-- Dumping data for table juezdb.concursos: ~2 rows (approximately)

-- Dumping structure for table juezdb.concursos_problemas
CREATE TABLE IF NOT EXISTS `concursos_problemas` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `concurso_id` int unsigned NOT NULL,
  `problema_id` int unsigned NOT NULL,
  `orden_problema` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `concurso_id` (`concurso_id`),
  KEY `problema_id` (`problema_id`),
  CONSTRAINT `fk_concursosprob_concurso` FOREIGN KEY (`concurso_id`) REFERENCES `concursos` (`id`),
  CONSTRAINT `fk_concursosprob_problema` FOREIGN KEY (`problema_id`) REFERENCES `problemas` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=110 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_spanish_ci;

-- Dumping data for table juezdb.concursos_problemas: ~0 rows (approximately)

-- Dumping structure for table juezdb.envios
CREATE TABLE IF NOT EXISTS `envios` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `usuario_id` int unsigned NOT NULL,
  `problema_id` int unsigned NOT NULL,
  `concurso_id` int unsigned DEFAULT NULL,
  `lenguaje_id` int unsigned NOT NULL,
  `codigo_fuente` text CHARACTER SET utf8mb4 COLLATE utf8mb4_spanish_ci NOT NULL,
  `veredicto_id` int unsigned DEFAULT NULL,
  `tiempo_ejecucion` float DEFAULT NULL,
  `memoria_usada` int DEFAULT NULL,
  `enviado_en` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `usuario_id` (`usuario_id`),
  KEY `problema_id` (`problema_id`),
  KEY `concurso_id` (`concurso_id`),
  KEY `lenguaje_id` (`lenguaje_id`),
  KEY `veredicto_id` (`veredicto_id`),
  CONSTRAINT `fk_envios_concurso` FOREIGN KEY (`concurso_id`) REFERENCES `concursos` (`id`),
  CONSTRAINT `fk_envios_lenguaje` FOREIGN KEY (`lenguaje_id`) REFERENCES `lenguajes` (`id`),
  CONSTRAINT `fk_envios_problema` FOREIGN KEY (`problema_id`) REFERENCES `problemas` (`id`),
  CONSTRAINT `fk_envios_usuario` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`),
  CONSTRAINT `fk_envios_veredicto` FOREIGN KEY (`veredicto_id`) REFERENCES `veredictos` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=101 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_spanish_ci;

-- Dumping data for table juezdb.envios: ~5 rows (approximately)

-- Dumping structure for table juezdb.inscripciones
CREATE TABLE IF NOT EXISTS `inscripciones` (
  `usuario_id` int unsigned NOT NULL,
  `concurso_id` int unsigned NOT NULL,
  `fecha_inscripcion` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`usuario_id`,`concurso_id`),
  KEY `fk_inscripciones_concurso` (`concurso_id`),
  CONSTRAINT `fk_inscripciones_concurso` FOREIGN KEY (`concurso_id`) REFERENCES `concursos` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_inscripciones_usuario` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Dumping data for table juezdb.inscripciones: ~0 rows (approximately)

-- Dumping structure for table juezdb.lenguajes
CREATE TABLE IF NOT EXISTS `lenguajes` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `nombre` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_spanish_ci NOT NULL,
  `comando_compilar` text COLLATE utf8mb4_spanish_ci,
  `extension_archivo` varchar(10) COLLATE utf8mb4_spanish_ci DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_spanish_ci;

-- Dumping data for table juezdb.lenguajes: ~3 rows (approximately)
INSERT INTO `lenguajes` (`id`, `nombre`, `comando_compilar`, `extension_archivo`) VALUES
	(1, 'Python', NULL, '.py'),
	(2, 'java', NULL, '.java'),
	(3, 'C++', NULL, '.cpp');

-- Dumping structure for table juezdb.problemas
CREATE TABLE IF NOT EXISTS `problemas` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `codigo` varchar(20) COLLATE utf8mb4_spanish_ci NOT NULL,
  `titulo` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_spanish_ci NOT NULL,
  `descripcion` text COLLATE utf8mb4_spanish_ci,
  `descripcion_entrada` text COLLATE utf8mb4_spanish_ci,
  `descripcion_salida` text COLLATE utf8mb4_spanish_ci,
  `limite_tiempo` int DEFAULT NULL,
  `limite_memoria` int DEFAULT NULL,
  `entrada_ejemplo` text COLLATE utf8mb4_spanish_ci,
  `salida_ejemplo` text COLLATE utf8mb4_spanish_ci,
  `autor_id` int unsigned DEFAULT NULL,
  `es_publico` tinyint(1) DEFAULT NULL,
  `fecha_creacion` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `codigo` (`codigo`),
  KEY `fk_autor` (`autor_id`),
  CONSTRAINT `fk_autor` FOREIGN KEY (`autor_id`) REFERENCES `usuarios` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_spanish_ci;

-- Dumping data for table juezdb.problemas: ~1 rows (approximately)

-- Dumping structure for table juezdb.roles
CREATE TABLE IF NOT EXISTS `roles` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `nombre` varchar(50) COLLATE utf8mb4_spanish_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `nombre` (`nombre`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_spanish_ci;

-- Dumping data for table juezdb.roles: ~2 rows (approximately)
INSERT INTO `roles` (`id`, `nombre`) VALUES
	(1, 'administrador'),
	(2, 'usuario');

-- Dumping structure for table juezdb.usuarios
CREATE TABLE IF NOT EXISTS `usuarios` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `nombre_usuario` varchar(50) COLLATE utf8mb4_spanish_ci NOT NULL,
  `correo` varchar(100) COLLATE utf8mb4_spanish_ci NOT NULL,
  `contrasena_hash` varchar(200) COLLATE utf8mb4_spanish_ci NOT NULL,
  `rol_id` int unsigned NOT NULL,
  `fecha_registro` datetime DEFAULT NULL,
  `activo` tinyint(1) NOT NULL DEFAULT '1',
  PRIMARY KEY (`id`),
  UNIQUE KEY `nombre_usuario` (`nombre_usuario`),
  UNIQUE KEY `correo` (`correo`),
  KEY `rol_id` (`rol_id`),
  CONSTRAINT `fk_usuarios_rol` FOREIGN KEY (`rol_id`) REFERENCES `roles` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_spanish_ci;

-- Dumping data for table juezdb.usuarios: ~4 rows (approximately)
INSERT INTO `usuarios` (`id`, `nombre_usuario`, `correo`, `contrasena_hash`, `rol_id`, `fecha_registro`, `activo`) VALUES
	(3, 'lyria', 'java.lyria@gmail.com', 'scrypt:32768:8:1$Hp2dlZZ8G6Fz7FlW$6a48c227c841ec2e3e87b022abf122ba6d9a011685acb25bd4070de68d8a3cf733472237eb3cb257ee956a6a9259dd34756c36fd2468e35ccf488aa055cf9750', 1, '2025-06-24 17:58:57', 1),
	(4, 'root', 'freddyraquel12@gmail.com', 'scrypt:32768:8:1$DaG7z0Tt3JOyoguV$849ad5eb8907611ae118251efb4006e392e1ecfc4019e7735298fe14da1b67be7d432537130668673d44a8d54b304adc3838796522f843113660a4d0f0f80c25', 2, '2025-06-26 15:47:18', 1),
	(5, 'admin', 'freddyraquel13@gmail.com', 'scrypt:32768:8:1$G3xk35HDIhtHAYje$10fc667e7f6447c9697c86913c3d831ab6324be6e4561941256b00a21fe5b215a3ba9fa7682553cb3c39f63e3275319c5cbd65c463579dce22f3df886b5e92e9', 1, '2025-06-29 03:36:47', 1),
	(6, 'aiko', 'aiko.267@gmail.com', 'scrypt:32768:8:1$zMMYrGKd2rFduCxc$dffd73dbe7d669318491787e0512169351aaeb8917ce832dbc9ba2f070c4753997e99ebb4ef9c291f26f0d353bf0eb565322097471ddd48239a81b3ee2e95446', 2, '2025-07-02 15:58:24', 1);

-- Dumping structure for table juezdb.veredictos
CREATE TABLE IF NOT EXISTS `veredictos` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `codigo` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_spanish_ci NOT NULL,
  `descripcion` varchar(100) COLLATE utf8mb4_spanish_ci DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_spanish_ci;

-- Dumping data for table juezdb.veredictos: ~8 rows (approximately)
INSERT INTO `veredictos` (`id`, `codigo`, `descripcion`) VALUES
	(1, 'AC', 'Aceptado'),
	(2, 'WA', 'Respuesta incorrecta'),
	(3, 'TLE', 'Tiempo límite excedido'),
	(4, 'MLE', 'Memoria límite excedida'),
	(5, 'RE', 'Error en tiempo de ejecución'),
	(6, 'CE', 'Error de compilación'),
	(7, 'PE', 'Error de formato'),
	(8, 'IE', 'Error interno');

/*!40103 SET TIME_ZONE=IFNULL(@OLD_TIME_ZONE, 'system') */;
/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IFNULL(@OLD_FOREIGN_KEY_CHECKS, 1) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40111 SET SQL_NOTES=IFNULL(@OLD_SQL_NOTES, 1) */;
