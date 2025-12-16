# Heritage Rover Works - Sistema de Gestión de Restauración

Proyecto para la asignatura Administración y Diseño de Bases de Datos.
Sistema de gestión integral para un taller especializado en Land Rovers clásicos. La aplicación permite controlar el inventario de piezas, gestionar proyectos de restauración, administrar expediciones/rodajes y mantener un registro de clientes y vehículos.

## Integrantes del equipo:

* Alejandro Rodríguez Rojas
* Aitor Manuel Perdomo Hermida
* Javier Francisco Díaz

## Características del Sistema

* **Dashboard General:** Visualización de KPIs en tiempo real (Total vehículos, Proyectos activos, Valor de stock, Coches en rodaje).
* **Gestión de Personas:** Alta y baja de Clientes y Empleados con roles diferenciados.
* **Flota de Vehículos:** Registro de Land Rovers clásicos asignados a sus propietarios.
* **Proyectos de Taller:** Gestión de restauraciones asignando vehículos y supervisores (Cumpliendo restricción de Inclusividad).
* **Gestión de Rodajes:** Envío de vehículos a rodajes de cine (Controlado por restricción de Exclusión: un coche en taller no puede ir a rodaje).
* **Almacén Inteligente:** Gestión de catálogo de piezas y compras a proveedores con actualización automática de stock (Triggers).

## Requisitos Previos

* PostgreSQL (Servidor de base de datos)
* Python 3.x
* pip (Gestor de paquetes de Python)

## 1. Configuración de la Base de Datos

Para desplegar la base de datos, ejecuta los scripts SQL en el siguiente orden estricto desde la raíz del proyecto.

Abre una terminal en la carpeta del proyecto y ejecuta:

### Crear la base de datos y el esquema (Tablas):

```bash
sudo -u postgres psql -f sql/schema.sql
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

### (Opcional) Tests de validación:

```bash
sudo -u postgres psql -d landrovers -f sql/tests.sql
```

## 2. Configuración de la Aplicación (Flask)

### Configurar credenciales:
Asegúrate de que en el archivo `app/app.py` la contraseña de la base de datos es correcta:

```python
DB_CONFIG = {
    'dbname': 'landrovers',
    'user': 'postgres',
    'password': 'tu_contrasena', # <--- REVISAR
    'host': 'localhost'
}
```

### Instalar dependencias:
Desde la raíz del proyecto:

```bash
# Crear entorno virtual (opcional pero recomendado)
python3 -m venv venv
source venv/bin/activate

# Instalar librerias
pip install flask psycopg2-binary
```

### Ejecutar el servidor:

```bash
python3 app/app.py
```

## 3. Uso de la Aplicación Web

Una vez iniciado el servidor, abre tu navegador web e ingresa a:

http://localhost:5000

Desde la interfaz web podrás navegar por las siguientes pestañas:

* **Dashboard:** Vista general del estado del taller.
* **Personas:** Formulario inteligente para registrar Clientes (datos bancarios) o Empleados (datos seguridad social).
* **Flota:** Inventario de vehículos. Solo permite asignar vehículos a clientes existentes.
* **Proyectos & Rodajes:**
    * *Panel izquierdo:* Crear proyectos de taller (asigna supervisor) o enviar a rodaje.
    * *Panel derecho:* Listado de restauraciones en curso y expediciones activas.
    * *Prueba de Exclusión:* Intenta enviar a rodaje un coche que ya tenga un proyecto abierto para verificar el bloqueo por Trigger.
* **Almacén:**
    * Gestión de referencias de piezas.
    * Simulador de compras: Al comprar stock, se verifica el aumento automático en la tabla de piezas (Trigger de Stock).

## 4. Ejemplos de uso de la API (cURL)

Además de la web, puedes interactuar directamente con la API REST utilizando curl desde la terminal.

### Gestión de Vehículos

**Listar todos:**

```bash
curl -X GET http://localhost:5000/api/vehiculos
```

**Crear vehículo:**

```bash
curl -X POST http://localhost:5000/api/vehiculos \
     -H "Content-Type: application/json" \
     -d '{"VIN": "TEST001", "Matricula": "TF-TEST", "Anio": 2024, "Color_Original": "Blanco", "Tipo_Motor": "V8", "DNI_Propietario": "11111111A"}'
```

**Eliminar vehículo:**

```bash
curl -X DELETE http://localhost:5000/api/vehiculos/TEST001
```

### Gestión de Personas

**Listar personas (con rol):**

```bash
curl -X GET http://localhost:5000/api/personas
```

**Crear Cliente:**

```bash
curl -X POST http://localhost:5000/api/personas \
     -H "Content-Type: application/json" \
     -d '{"DNI": "99999999Z", "Nombre": "Juan", "Apellidos": "Perez", "Email": "juan@test.com", "Telefono": "600", "Rol": "Cliente", "Num_Cuenta": "ES99..."}'
```

**Eliminar Persona:**

```bash
curl -X DELETE http://localhost:5000/api/personas/99999999Z
```

### Gestión de Proyectos

**Listar Proyectos:**

```bash
curl -X GET http://localhost:5000/api/proyectos
```

**Crear Proyecto (Asigna Supervisor automáticamente):**
(Asegúrate de usar un VIN y un DNI de Empleado existentes)

```bash
curl -X POST http://localhost:5000/api/proyectos \
     -H "Content-Type: application/json" \
     -d '{"Nombre": "Restauracion Express", "VIN": "SALLHV123456", "Supervisor": "44444444D"}'
```

**Eliminar Proyecto:**
(Sustituye 1 por el ID del proyecto)

```bash
curl -X DELETE http://localhost:5000/api/proyectos/1
```

### Gestión de Piezas (Almacén)

**Listar Piezas:**

```bash
curl -X GET http://localhost:5000/api/piezas
```

**Crear Nueva Referencia:**

```bash
curl -X POST http://localhost:5000/api/piezas \
     -H "Content-Type: application/json" \
     -d '{"Ref_Pieza": "NEW001", "Nombre": "Faros LED", "Descripcion": "Modernos", "Stock_Inicial": 10}'
```

**Eliminar Pieza:**

```bash
curl -X DELETE http://localhost:5000/api/piezas/NEW001
```

### Pruebas de Triggers y Rodajes

**Comprar Pieza (Trigger Stock Auto):**

```bash
curl -X POST http://localhost:5000/api/comprar_pieza \
     -H "Content-Type: application/json" \
     -d '{"Ref_Pieza": "GME123", "Cantidad": 5}'
```

**Listar Rodajes Activos:**

```bash
curl -X GET http://localhost:5000/api/rodajes
```

**Enviar a Rodaje (Prueba Exclusión):**
(Si el coche tiene proyecto activo, devolverá error)

```bash
curl -X POST http://localhost:5000/api/enviar_rodaje \
     -H "Content-Type: application/json" \
     -d '{"VIN": "TEST001", "Coste": 1500}'
```

**Finalizar/Borrar Rodaje:**
(Sustituye VIN e ID_Rodaje)

```bash
curl -X DELETE http://localhost:5000/api/rodajes/TEST001/1
```

## Estructura del Proyecto

* `sql/`: Directorio con los scripts SQL para la base de datos.
    * `schema.sql`: Definición de tablas y restricciones.
    * `data.sql`: Datos de prueba iniciales.
    * `logic.sql`: Procedimientos almacenados, funciones y triggers.
    * `queries.sql`: Consultas de ejemplo.
    * `tests.sql`: Tests de validación de reglas de negocio.
* `app/`: Código fuente de la aplicación web.
    * `app.py`: Servidor Flask y endpoints de la API REST.
    * `templates/`: Plantillas HTML para la interfaz de usuario.
* `docs/`: Documentación del proyecto.
    * `ENTIDAD-RELACION.drawio`: Diagrama E-R de la base de datos.
* `venv/`: Entorno virtual de Python (generado localmente).

