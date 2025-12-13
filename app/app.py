from flask import Flask, request, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

# CONFIGURACIÓN DE LA BASE DE DATOS
# ¡¡IMPORTANTE!!: Cambia la contraseña si pusiste otra
DB_CONFIG = {
    'dbname': 'landrovers',
    'user': 'postgres',
    'password': 'postgres', 
    'host': 'localhost'
}

def get_db_connection():
    conn = psycopg2.connect(**DB_CONFIG)
    return conn

@app.route('/')
def home():
    return "<h1>API Heritage Rover Works</h1><p>Sistema funcionando correctamente.</p>"

# ------------------------------------------------------------------
# 1. READ (Leer todos los vehículos) - GET
# ------------------------------------------------------------------
@app.route('/vehiculos', methods=['GET'])
def get_vehiculos():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute('SELECT * FROM VEHICULO;')
    vehiculos = cur.fetchall()
    
    cur.close()
    conn.close()
    return jsonify(vehiculos)

# ------------------------------------------------------------------
# 2. READ (Leer un solo vehículo por VIN) - GET
# ------------------------------------------------------------------
@app.route('/vehiculos/<vin>', methods=['GET'])
def get_vehiculo_by_vin(vin):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute('SELECT * FROM VEHICULO WHERE VIN = %s;', (vin,))
    vehiculo = cur.fetchone()
    
    cur.close()
    conn.close()
    
    if vehiculo:
        return jsonify(vehiculo)
    else:
        return jsonify({'error': 'Vehiculo no encontrado'}), 404

# ------------------------------------------------------------------
# 3. CREATE (Insertar un nuevo vehículo) - POST
# ------------------------------------------------------------------
@app.route('/vehiculos', methods=['POST'])
def create_vehiculo():
    new_car = request.get_json()
    
    # Validamos que vengan los datos obligatorios
    if not new_car or 'VIN' not in new_car or 'DNI_Propietario' not in new_car:
         return jsonify({'error': 'Faltan datos obligatorios (VIN, DNI_Propietario)'}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            INSERT INTO VEHICULO (VIN, Matricula, Anio, Color_Original, Tipo_Motor, DNI_Propietario)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING VIN;
        """, (new_car['VIN'], new_car['Matricula'], new_car['Anio'], 
              new_car['Color_Original'], new_car['Tipo_Motor'], new_car['DNI_Propietario']))
        
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'message': 'Vehiculo creado con exito', 'VIN': new_car['VIN']}), 201
        
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 400

# ------------------------------------------------------------------
# 4. UPDATE (Actualizar datos de un vehículo) - PUT
# ------------------------------------------------------------------
@app.route('/vehiculos/<vin>', methods=['PUT'])
def update_vehiculo(vin):
    data = request.get_json()
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Ejemplo: Actualizamos solo el Color y el Motor
    cur.execute("""
        UPDATE VEHICULO 
        SET Color_Original = %s, Tipo_Motor = %s
        WHERE VIN = %s;
    """, (data['Color_Original'], data['Tipo_Motor'], vin))
    
    updated_rows = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()
    
    if updated_rows > 0:
        return jsonify({'message': 'Vehiculo actualizado correctamente'})
    else:
        return jsonify({'error': 'Vehiculo no encontrado'}), 404

# ------------------------------------------------------------------
# 5. DELETE (Borrar un vehículo) - DELETE
# ------------------------------------------------------------------
@app.route('/vehiculos/<vin>', methods=['DELETE'])
def delete_vehiculo(vin):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute('DELETE FROM VEHICULO WHERE VIN = %s;', (vin,))
        deleted_rows = cur.rowcount
        conn.commit()
        
        if deleted_rows > 0:
            return jsonify({'message': 'Vehiculo eliminado'})
        else:
            return jsonify({'error': 'Vehiculo no encontrado'}), 404
            
    except Exception as e:
        # Probablemente falle si intentas borrar un coche con proyectos (FK constraint)
        return jsonify({'error': 'No se puede borrar: ' + str(e)}), 400
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    # Ejecutamos en el puerto 5000 y accesible desde cualquier IP (0.0.0.0)
    app.run(host='0.0.0.0', port=5000, debug=True)