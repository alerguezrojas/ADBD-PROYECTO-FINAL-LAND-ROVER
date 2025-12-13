# Heritage Rover Works - Sistema de Gestión de Restauración

Proyecto para la asignatura Administración y Diseño de Bases de Datos.
Sistema de gestión para un taller especializado en Land Rovers clásicos, incluyendo control de inventario, proyectos de restauración, expediciones y API REST.

## Integrantes del equipo:

* Alejandro Rodríguez Rojas
* Aitor Manuel Perdomo Hermida
* Javier Francisco Díaz

## Requisitos Previos

* PostgreSQL
* Python 3.x
* pip

## 1. Configuración de la Base de Datos

Para desplegar la base de datos, ejecuta los scripts SQL en el siguiente orden desde la raíz del proyecto.

Abre una terminal en la carpeta del proyecto y ejecuta:

### Crear el esquema (Tablas):

```bash
sudo -u postgres psql -d landrovers -f sql/schema.sql
```

### Cargar datos de prueba:

```bash
sudo -u postgres psql -d landrovers -f sql/data.sql
```

### Cargar la lógica (Triggers y Funciones):

```bash
sudo -u postgres psql -d landrovers -f sql/logic.sql
```

### (Opcional) Consultas de prueba:

```bash
sudo -u postgres psql -d landrovers -f sql/queries.sql
```

## 2. Configuración de la API (Flask)

### Configurar credenciales:
Asegúrate de que en el archivo `app/app.py` la contraseña de la base de datos es correcta:

```python
DB_CONFIG = {
    'dbname': 'landrovers',
    'user': 'postgres',
    'password': 'tu_contrasena',
    'host': 'localhost'
}
```

### Instalar dependencias:
Desde la raíz del proyecto:

```bash
source venv/bin/activate
pip install flask psycopg2-binary
```

### Ejecutar el servidor:

```bash
python3 app/app.py
```

La API estará disponible en http://localhost:5000

## 3. Pruebas de la API

Puedes probar los endpoints utilizando curl en otra terminal mientras el servidor está corriendo.

### Obtener todos los vehículos (GET):

```bash
curl -X GET http://localhost:5000/vehiculos
```

### Insertar un nuevo vehículo (POST):

```bash
curl -X POST http://localhost:5000/vehiculos \
     -H "Content-Type: application/json" \
     -d '{"VIN": "TEST001", "Matricula": "TF-TEST", "Anio": 2024, "Color_Original": "Blanco", "Tipo_Motor": "V8", "DNI_Propietario": "11111111A"}'
```

### Actualizar un vehículo (PUT):

```bash
curl -X PUT http://localhost:5000/vehiculos/TEST001 \
     -H "Content-Type: application/json" \
     -d '{"Color_Original": "Verde Militar", "Tipo_Motor": "V8 3.9"}'
```

### Borrar el vehículo de prueba (DELETE):

```bash
curl -X DELETE http://localhost:5000/vehiculos/TEST001
```

## Estructura del Proyecto

* `sql/`: Scripts de base de datos.
* `app/`: Código fuente de la aplicación Flask.
* `venv/`: Entorno virtual de Python.
