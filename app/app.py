from flask import Flask, request, jsonify, render_template
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

# CONFIGURACIÓN DE LA BASE DE DATOS
DB_CONFIG = {
    'dbname': 'landrovers',
    'user': 'postgres',
    'password': 'postgres', # <--- REVISA TU CONTRASEÑA
    'host': 'localhost'
}

def get_db_connection():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"Error conexión BD: {e}")
        return None

@app.route('/')
def home():
    return render_template('index.html')

# ==========================================
# 1. DASHBOARD
# ==========================================
@app.route('/api/dashboard', methods=['GET'])
def get_dashboard_stats():
    conn = get_db_connection()
    if not conn: return jsonify({'error': 'Error conexión BD'}), 500
    cur = conn.cursor()
    stats = {}
    try:
        cur.execute("SELECT COUNT(*) FROM VEHICULO;")
        stats['vehiculos'] = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM PROYECTO WHERE Fecha_Fin IS NULL;")
        stats['proyectos_activos'] = cur.fetchone()[0]
        cur.execute("SELECT COALESCE(SUM(Stock_Actual), 0) FROM PIEZA;")
        stats['piezas_stock'] = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM ASISTE_A WHERE Fecha_Fin >= CURRENT_DATE;")
        stats['en_rodaje'] = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM CLIENTE;")
        stats['clientes'] = cur.fetchone()[0]
    except Exception as e:
        print(e)
    finally:
        cur.close()
        conn.close()
    return jsonify(stats)

# ==========================================
# 2. GESTIÓN DE PERSONAS (ROBUSTO)
# ==========================================
@app.route('/api/personas', methods=['GET'])
def get_personas():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    query = """
        SELECT P.*, 
               CASE 
                   WHEN C.DNI_Cliente IS NOT NULL THEN 'Cliente' 
                   WHEN E.DNI_Empleado IS NOT NULL THEN 'Empleado' 
                   ELSE 'Desconocido'
               END as Rol,
               C.Num_Cuenta, C.Fecha_Alta,
               E.NSS, E.Salario, E.Fecha_Contratacion
        FROM PERSONA P
        LEFT JOIN CLIENTE C ON P.DNI = C.DNI_Cliente
        LEFT JOIN EMPLEADO E ON P.DNI = E.DNI_Empleado
        ORDER BY P.Apellidos;
    """
    cur.execute(query)
    data = cur.fetchall()
    conn.close()
    return jsonify(data)

@app.route('/api/personas', methods=['POST'])
def create_persona():
    data = request.get_json()
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Validación de campos obligatorios
        dni = data.get('DNI')
        nombre = data.get('Nombre')
        if not dni or not nombre:
            return jsonify({'error': 'Faltan datos: DNI y Nombre son obligatorios'}), 400

        # Insertar en PERSONA
        cur.execute("""
            INSERT INTO PERSONA (DNI, Nombre, Apellidos, Email, Telefono)
            VALUES (%s, %s, %s, %s, %s)
        """, (dni, nombre, data.get('Apellidos', ''), data.get('Email', ''), data.get('Telefono', '')))
        
        # Insertar en Subtipo
        role = data.get('Rol', 'Cliente')
        if role == 'Cliente':
            cur.execute("INSERT INTO CLIENTE (DNI_Cliente, Num_Cuenta, Fecha_Alta) VALUES (%s, %s, CURRENT_DATE)", 
                       (dni, data.get('Num_Cuenta', '')))
        elif role == 'Empleado':
            salario = data.get('Salario')
            if salario == '': salario = 0
            cur.execute("INSERT INTO EMPLEADO (DNI_Empleado, NSS, Salario, Fecha_Contratacion) VALUES (%s, %s, %s, CURRENT_DATE)", 
                       (dni, data.get('NSS', ''), salario))
            
        conn.commit()
        return jsonify({'msg': f"{role} registrado correctamente"})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 400
    finally:
        conn.close()

@app.route('/api/personas/<dni>', methods=['DELETE'])
def delete_persona(dni):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Intento de borrado limpio
        cur.execute("DELETE FROM CLIENTE WHERE DNI_Cliente = %s", (dni,))
        cur.execute("DELETE FROM EMPLEADO WHERE DNI_Empleado = %s", (dni,))
        cur.execute("DELETE FROM PERSONA WHERE DNI = %s", (dni,))
        conn.commit()
        return jsonify({'msg': 'Persona eliminada'})
    except psycopg2.IntegrityError:
        conn.rollback()
        # Mensaje amigable si falla FK
        return jsonify({'error': 'No se puede eliminar: Esta persona tiene Vehículos o Proyectos activos.'}), 400
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 400
    finally:
        conn.close()

# ==========================================
# 3. GESTIÓN DE VEHÍCULOS (CORREGIDO CURL)
# ==========================================
@app.route('/api/vehiculos', methods=['GET'])
def get_vehiculos():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    query = """
        SELECT V.*, P.Nombre || ' ' || P.Apellidos as Nombre_Propietario 
        FROM VEHICULO V
        JOIN CLIENTE C ON V.DNI_Propietario = C.DNI_Cliente
        JOIN PERSONA P ON C.DNI_Cliente = P.DNI
        ORDER BY V.Anio ASC;
    """
    cur.execute(query)
    data = cur.fetchall()
    conn.close()
    return jsonify(data)

@app.route('/api/vehiculos', methods=['POST'])
def create_vehiculo():
    data = request.get_json()
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # LÓGICA FLEXIBLE: Acepta nombres de campo de la Web Y de la BD (cURL)
        vin = data.get('VIN')
        matricula = data.get('Matricula')
        anio = data.get('Anio', 0)
        
        # Busca 'Color' (Web) O 'Color_Original' (cURL)
        color = data.get('Color') or data.get('Color_Original', '')
        
        # Busca 'Motor' (Web) O 'Tipo_Motor' (cURL)
        motor = data.get('Motor') or data.get('Tipo_Motor', '')
        
        # Busca 'DNI' (Web) O 'DNI_Propietario' (cURL)
        dni = data.get('DNI') or data.get('DNI_Propietario')

        if not vin or not dni:
             return jsonify({'error': 'Faltan datos obligatorios (VIN, DNI)'}), 400

        cur.execute("""
            INSERT INTO VEHICULO (VIN, Matricula, Anio, Color_Original, Tipo_Motor, DNI_Propietario)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (vin, matricula, anio, color, motor, dni))
        
        conn.commit()
        return jsonify({'msg': 'Vehiculo creado correctamente'})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 400
    finally:
        conn.close()

@app.route('/api/vehiculos/<vin>', methods=['DELETE'])
def delete_vehiculo(vin):
    """
    Borrado en cascada manual para evitar errores de integridad
    """
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # 1. Limpiar proyectos asociados y sus dependencias
        cur.execute("SELECT ID_Proyecto FROM PROYECTO WHERE VIN_Vehiculo = %s", (vin,))
        proyectos = cur.fetchall()
        for row in proyectos:
            pid = row[0]
            cur.execute("DELETE FROM SUMINISTRA WHERE ID_Proyecto = %s", (pid,))
            cur.execute("DELETE FROM TRABAJA_EN WHERE ID_Proyecto = %s", (pid,))
            cur.execute("DELETE FROM FASE WHERE ID_Proyecto = %s", (pid,))
            cur.execute("DELETE FROM PROYECTO WHERE ID_Proyecto = %s", (pid,))

        # 2. Limpiar rodajes
        cur.execute("DELETE FROM ASISTE_A WHERE VIN = %s", (vin,))

        # 3. Borrar el coche
        cur.execute("DELETE FROM VEHICULO WHERE VIN = %s", (vin,))
        
        conn.commit()
        return jsonify({'msg': 'Vehiculo y su historial eliminados'})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': 'Error al eliminar: ' + str(e)}), 400
    finally:
        conn.close()

# ==========================================
# 4. GESTIÓN DE PROYECTOS
# ==========================================
@app.route('/api/proyectos', methods=['GET'])
def get_proyectos():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    query = """
        SELECT PR.ID_Proyecto, PR.Nombre_Descriptivo, PR.Fecha_Inicio, 
               V.Matricula, PE.Nombre || ' ' || PE.Apellidos as Supervisor
        FROM PROYECTO PR
        JOIN VEHICULO V ON PR.VIN_Vehiculo = V.VIN
        JOIN EMPLEADO E ON PR.DNI_Supervisor = E.DNI_Empleado
        JOIN PERSONA PE ON E.DNI_Empleado = PE.DNI
        ORDER BY PR.Fecha_Inicio DESC;
    """
    cur.execute(query)
    data = cur.fetchall()
    conn.close()
    return jsonify(data)

@app.route('/api/proyectos', methods=['POST'])
def create_proyecto():
    data = request.get_json()
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO PROYECTO (Nombre_Descriptivo, Fecha_Inicio, VIN_Vehiculo, DNI_Supervisor)
            VALUES (%s, CURRENT_DATE, %s, %s)
            RETURNING ID_Proyecto;
        """, (data['Nombre'], data['VIN'], data['Supervisor']))
        id_proyecto = cur.fetchone()[0]
        
        # Auto-asignación para cumplir Inclusividad
        cur.execute("INSERT INTO TRABAJA_EN (DNI_Empleado, ID_Proyecto, Horas_Dedicadas) VALUES (%s, %s, 0)", 
                   (data['Supervisor'], id_proyecto))

        conn.commit()
        return jsonify({'msg': 'Proyecto abierto correctamente'})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 400
    finally:
        conn.close()

@app.route('/api/proyectos/<id>', methods=['DELETE'])
def delete_proyecto(id):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Limpieza manual de hijos
        cur.execute("DELETE FROM SUMINISTRA WHERE ID_Proyecto = %s", (id,))
        cur.execute("DELETE FROM TRABAJA_EN WHERE ID_Proyecto = %s", (id,))
        cur.execute("DELETE FROM FASE WHERE ID_Proyecto = %s", (id,))
        cur.execute("DELETE FROM PROYECTO WHERE ID_Proyecto = %s", (id,))
        conn.commit()
        return jsonify({'msg': 'Proyecto eliminado'})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 400
    finally:
        conn.close()

# ==========================================
# 5. PIEZAS Y COMPRA (CORREGIDO ERROR SIN PROYECTOS)
# ==========================================
@app.route('/api/piezas', methods=['GET'])
def get_piezas():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM PIEZA ORDER BY Ref_Pieza ASC;")
    data = cur.fetchall()
    conn.close()
    return jsonify(data)

@app.route('/api/piezas', methods=['POST'])
def create_pieza():
    data = request.get_json()
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO PIEZA (Ref_Pieza, Nombre, Descripcion, Stock_Actual) VALUES (%s, %s, %s, %s)", 
                   (data['Ref_Pieza'], data['Nombre'], data.get('Descripcion', ''), data.get('Stock_Inicial', 0)))
        conn.commit()
        return jsonify({'msg': 'Referencia creada'})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 400
    finally:
        conn.close()

@app.route('/api/piezas/<ref>', methods=['DELETE'])
def delete_pieza(ref):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM SUMINISTRA WHERE Ref_Pieza = %s", (ref,))
        cur.execute("DELETE FROM COMPATIBILIDAD WHERE Ref_Pieza = %s", (ref,))
        cur.execute("DELETE FROM PIEZA WHERE Ref_Pieza = %s", (ref,))
        conn.commit()
        return jsonify({'msg': 'Pieza eliminada'})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': 'No se puede eliminar (referenciada en historial)'}), 400
    finally:
        conn.close()

@app.route('/api/comprar_pieza', methods=['POST'])
def comprar_pieza():
    """
    CORRECCIÓN: Valida si hay un proyecto activo antes de intentar insertar.
    """
    data = request.get_json()
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # 1. Intentamos buscar el último proyecto activo para asignar la compra
        cur.execute("SELECT ID_Proyecto FROM PROYECTO ORDER BY ID_Proyecto DESC LIMIT 1;")
        res = cur.fetchone()
        
        # Si no hay proyectos, detenemos la operación con un error útil
        if not res:
            return jsonify({'error': 'ERROR DE NEGOCIO: No existe ningún proyecto activo en el sistema. Según el diseño (Relación Ternaria), toda compra de material debe asignarse a un Proyecto de restauración. Por favor, crea primero un Proyecto.'}), 400
            
        pid = res[0]
        
        # 2. Insertamos usando el ID de proyecto encontrado
        cur.execute("INSERT INTO SUMINISTRA (CIF_Proveedor, Ref_Pieza, ID_Proyecto, Precio_Compra, Fecha_Suministro, Cantidad) VALUES ('B12345678', %s, %s, 50.00, CURRENT_DATE, %s)", 
                   (data['Ref_Pieza'], pid, data['Cantidad']))
        
        conn.commit()
        return jsonify({'msg': f"Compra registrada correctamente (Asignada al Proyecto #{pid}). Stock aumentado."})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 400
    finally:
        conn.close()

# ==========================================
# 6. RODAJE
# ==========================================
@app.route('/api/rodajes', methods=['GET'])
def get_rodajes():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    query = """
        SELECT A.VIN, A.ID_Rodaje, A.Fecha_Inicio, A.Fecha_Fin, A.Coste_Alquiler,
               V.Matricula, R.Productora, R.Lugar
        FROM ASISTE_A A
        JOIN VEHICULO V ON A.VIN = V.VIN
        JOIN RODAJE R ON A.ID_Rodaje = R.ID_Rodaje
        ORDER BY A.Fecha_Inicio DESC;
    """
    cur.execute(query)
    data = cur.fetchall()
    conn.close()
    return jsonify(data)

@app.route('/api/enviar_rodaje', methods=['POST'])
def enviar_rodaje():
    data = request.get_json()
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO ASISTE_A (VIN, ID_Rodaje, Fecha_Inicio, Fecha_Fin, Coste_Alquiler) VALUES (%s, 1, CURRENT_DATE, CURRENT_DATE + 7, %s)", 
                   (data['VIN'], data['Coste']))
        conn.commit()
        return jsonify({'msg': 'Vehiculo enviado a rodaje.'})
    except psycopg2.InternalError as e:
        conn.rollback()
        return jsonify({'error': f"BLOQUEO BD: {e.pgerror}"}), 400
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 400
    finally:
        conn.close()

@app.route('/api/rodajes/<vin>/<id_rodaje>', methods=['DELETE'])
def delete_rodaje(vin, id_rodaje):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM ASISTE_A WHERE VIN = %s AND ID_Rodaje = %s", (vin, id_rodaje))
        conn.commit()
        return jsonify({'msg': 'Rodaje cancelado/finalizado'})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 400
    finally:
        conn.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)