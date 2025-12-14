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
# 1. DASHBOARD & ESTADÍSTICAS
# ==========================================
@app.route('/api/dashboard', methods=['GET'])
def get_dashboard_stats():
    conn = get_db_connection()
    cur = conn.cursor()
    stats = {}
    
    cur.execute("SELECT COUNT(*) FROM VEHICULO;")
    stats['vehiculos'] = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM PROYECTO WHERE Fecha_Fin IS NULL;")
    stats['proyectos_activos'] = cur.fetchone()[0]
    
    cur.execute("SELECT SUM(Stock_Actual) FROM PIEZA;")
    stats['piezas_stock'] = cur.fetchone()[0] or 0
    
    cur.execute("SELECT COUNT(*) FROM ASISTE_A WHERE Fecha_Fin >= CURRENT_DATE;")
    stats['en_rodaje'] = cur.fetchone()[0]

    cur.close()
    conn.close()
    return jsonify(stats)

# ==========================================
# 2. GESTIÓN DE PERSONAS
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
        cur.execute("""
            INSERT INTO PERSONA (DNI, Nombre, Apellidos, Email, Telefono)
            VALUES (%s, %s, %s, %s, %s)
        """, (data['DNI'], data['Nombre'], data['Apellidos'], data['Email'], data['Telefono']))
        
        if data['Rol'] == 'Cliente':
            cur.execute("INSERT INTO CLIENTE (DNI_Cliente, Num_Cuenta, Fecha_Alta) VALUES (%s, %s, CURRENT_DATE)", 
                       (data['DNI'], data['Num_Cuenta']))
        elif data['Rol'] == 'Empleado':
            cur.execute("INSERT INTO EMPLEADO (DNI_Empleado, NSS, Salario, Fecha_Contratacion) VALUES (%s, %s, %s, CURRENT_DATE)", 
                       (data['DNI'], data['NSS'], data['Salario']))
            
        conn.commit()
        return jsonify({'msg': f"{data['Rol']} registrado correctamente"})
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
        cur.execute("DELETE FROM CLIENTE WHERE DNI_Cliente = %s", (dni,))
        cur.execute("DELETE FROM EMPLEADO WHERE DNI_Empleado = %s", (dni,))
        cur.execute("DELETE FROM PERSONA WHERE DNI = %s", (dni,))
        conn.commit()
        return jsonify({'msg': 'Persona eliminada'})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': 'No se puede eliminar (tiene relaciones activas)'}), 400
    finally:
        conn.close()

# ==========================================
# 3. GESTIÓN DE VEHÍCULOS
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
        cur.execute("""
            INSERT INTO VEHICULO (VIN, Matricula, Anio, Color_Original, Tipo_Motor, DNI_Propietario)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (data['VIN'], data['Matricula'], data['Anio'], data['Color'], data['Motor'], data['DNI']))
        conn.commit()
        return jsonify({'msg': 'Vehículo creado correctamente'})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 400
    finally:
        conn.close()

@app.route('/api/vehiculos/<vin>', methods=['DELETE'])
def delete_vehiculo(vin):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM VEHICULO WHERE VIN = %s", (vin,))
        conn.commit()
        return jsonify({'msg': 'Vehículo eliminado'})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': 'No se puede eliminar (tiene historial)'}), 400
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
        
        # Cumplir inclusividad
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
        cur.execute("DELETE FROM PROYECTO WHERE ID_Proyecto = %s", (id,))
        conn.commit()
        return jsonify({'msg': 'Proyecto eliminado'})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 400
    finally:
        conn.close()

# ==========================================
# 5. GESTIÓN DE PIEZAS
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
                   (data['Ref_Pieza'], data['Nombre'], data['Descripcion'], data['Stock_Inicial']))
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
        cur.execute("DELETE FROM PIEZA WHERE Ref_Pieza = %s", (ref,))
        conn.commit()
        return jsonify({'msg': 'Pieza eliminada'})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': 'No se puede eliminar (en uso)'}), 400
    finally:
        conn.close()

@app.route('/api/comprar_pieza', methods=['POST'])
def comprar_pieza():
    data = request.get_json()
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO SUMINISTRA (CIF_Proveedor, Ref_Pieza, ID_Proyecto, Precio_Compra, Fecha_Suministro, Cantidad) VALUES ('B12345678', %s, 1, 50.00, CURRENT_DATE, %s)", 
                   (data['Ref_Pieza'], data['Cantidad']))
        conn.commit()
        return jsonify({'msg': f"Compra OK. Stock +{data['Cantidad']}."})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 400
    finally:
        conn.close()

# ==========================================
# 6. RODAJE (NUEVO: LISTAR Y BORRAR)
# ==========================================
@app.route('/api/rodajes', methods=['GET'])
def get_rodajes():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    # JOIN para ver detalles del coche y del rodaje
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
        return jsonify({'msg': 'Vehículo enviado a rodaje.'})
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