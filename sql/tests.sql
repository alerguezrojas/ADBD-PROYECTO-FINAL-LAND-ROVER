-- ===================================================================================
-- SCRIPT INTEGRAL DE PRUEBAS Y VALIDACIÓN - HERITAGE ROVER WORKS
-- Cobertura: 100% de tablas del sistema.
-- NOTA: Cada bloque incluye un paso final de REVERSIÓN para mantener la BD consistente.
-- ===================================================================================

-- -----------------------------------------------------------------------------------
-- BLOQUE 1: GESTIÓN DE PERSONAS Y ROLES (Tablas: PERSONA, CLIENTE, EMPLEADO)
-- Objetivo: Verificar la jerarquía IS_A, la inserción en tablas vinculadas y la integridad.
-- -----------------------------------------------------------------------------------

-- 1.1. Inserción de una nueva Persona en la superclase.
INSERT INTO PERSONA (DNI, Nombre, Apellidos, Email, Telefono) 
VALUES ('99999999Z', 'Test Persona', 'Apellido Test', 'test@mail.com', '600000000');

-- 1.2. Especialización: Registro de la entidad dependiente CLIENTE.
INSERT INTO CLIENTE (DNI_Cliente, Num_Cuenta, Fecha_Alta) 
VALUES ('99999999Z', 'ES000000000000000000', CURRENT_DATE);

-- 1.3. Verificación de la integridad de los datos mediante reunión natural (JOIN).
SELECT P.Nombre, P.Apellidos, C.Num_Cuenta 
FROM PERSONA P 
JOIN CLIENTE C ON P.DNI = C.DNI_Cliente 
WHERE P.DNI = '99999999Z';

-- 1.4. REVERSIÓN (Limpieza): Eliminación de los registros de prueba.
DELETE FROM CLIENTE WHERE DNI_Cliente = '99999999Z';
DELETE FROM PERSONA WHERE DNI = '99999999Z';


-- -----------------------------------------------------------------------------------
-- BLOQUE 2: CATÁLOGOS AUXILIARES (Tablas: MODELO_CATALOGO, PROVEEDOR, RODAJE)
-- Objetivo: Validación de operaciones CRUD en tablas maestras sin dependencias fuertes.
-- -----------------------------------------------------------------------------------

-- 2.1. Inserción de un nuevo registro en el catálogo de modelos.
INSERT INTO MODELO_CATALOGO (Nombre_Comercial) VALUES ('Land Rover Series I 86" (Versión Test)');

-- 2.2. Modificación (UPDATE) de un atributo en la tabla de proveedores.
UPDATE PROVEEDOR SET Web = 'www.britpart-updated-test.com' WHERE Nombre_Empresa LIKE 'Britpart%';

-- 2.3. Registro de un nuevo evento de Rodaje.
INSERT INTO RODAJE (Productora, Lugar) VALUES ('Test Productions', 'Desierto de Tabernas');

-- 2.4. Consulta de verificación de las operaciones DML realizadas.
SELECT * FROM MODELO_CATALOGO WHERE Nombre_Comercial LIKE '%(Versión Test)';
SELECT Nombre_Empresa, Web FROM PROVEEDOR WHERE Nombre_Empresa LIKE 'Britpart%';

-- 2.5. REVERSIÓN (Limpieza):
DELETE FROM MODELO_CATALOGO WHERE Nombre_Comercial LIKE '%(Versión Test)';
UPDATE PROVEEDOR SET Web = 'www.britpart.com' WHERE Nombre_Empresa LIKE 'Britpart%';
DELETE FROM RODAJE WHERE Productora = 'Test Productions';


-- -----------------------------------------------------------------------------------
-- BLOQUE 3: GESTIÓN DE VEHÍCULOS (Tabla: VEHICULO)
-- Objetivo: Verificación de persistencia en actualizaciones de atributos.
-- -----------------------------------------------------------------------------------

-- 3.1. Consulta del estado inicial (Color actual: 'Verde Inglés').
SELECT VIN, Matricula, Color_Original FROM VEHICULO WHERE Matricula = 'M-1234-OP';

-- 3.2. Actualización: Modificación del color del vehículo a 'Rojo Fuego'.
UPDATE VEHICULO SET Color_Original = 'Rojo Fuego' WHERE Matricula = 'M-1234-OP';

-- 3.3. Verificación del cambio de estado en la base de datos.
SELECT VIN, Matricula, Color_Original FROM VEHICULO WHERE Matricula = 'M-1234-OP';

-- 3.4. REVERSIÓN (Limpieza): Restauración del valor original.
UPDATE VEHICULO SET Color_Original = 'Verde Inglés' WHERE Matricula = 'M-1234-OP';


-- -----------------------------------------------------------------------------------
-- BLOQUE 4: INVENTARIO Y COMPATIBILIDAD (Tablas: PIEZA, COMPATIBILIDAD)
-- Objetivo: Gestión de relación M:N entre Piezas y Modelos.
-- -----------------------------------------------------------------------------------

-- 4.1. Alta de una nueva referencia de pieza en almacén.
INSERT INTO PIEZA (Ref_Pieza, Nombre, Descripcion, Stock_Actual) 
VALUES ('TEST-PART', 'Pieza Universal', 'Componente de prueba M:N', 10);

-- 4.2. Asignación de compatibilidad (M:N): Vinculación de la pieza con el Modelo ID 1.
INSERT INTO COMPATIBILIDAD (Ref_Pieza, ID_Modelo) VALUES ('TEST-PART', 1);

-- 4.3. Verificación de la integridad de la relación establecida.
SELECT P.Nombre as Pieza, M.Nombre_Comercial as Modelo 
FROM PIEZA P 
JOIN COMPATIBILIDAD C ON P.Ref_Pieza = C.Ref_Pieza
JOIN MODELO_CATALOGO M ON C.ID_Modelo = M.ID_Modelo
WHERE P.Ref_Pieza = 'TEST-PART';

-- 4.4. REVERSIÓN (Limpieza):
DELETE FROM COMPATIBILIDAD WHERE Ref_Pieza = 'TEST-PART';
DELETE FROM PIEZA WHERE Ref_Pieza = 'TEST-PART';


-- -----------------------------------------------------------------------------------
-- BLOQUE 5: PROYECTOS Y FASES (Tablas: PROYECTO, FASE, TRABAJA_EN)
-- Objetivo: Validación de restricciones CHECK y flujo de trabajo.
-- -----------------------------------------------------------------------------------

-- 5.1. Apertura de un Proyecto temporal para pruebas.
-- VIN: 'SALLHV654321', Supervisor: '33333333C'.
INSERT INTO PROYECTO (Nombre_Descriptivo, Fecha_Inicio, VIN_Vehiculo, DNI_Supervisor) 
VALUES ('Proyecto Test de Integridad', CURRENT_DATE, 'SALLHV654321', '33333333C');

-- 5.2. Asignación de recursos humanos (Tabla TRABAJA_EN).
-- Se asigna al propio supervisor para cumplir con la restricción de Inclusividad.
INSERT INTO TRABAJA_EN (DNI_Empleado, ID_Proyecto, Horas_Dedicadas) 
VALUES ('33333333C', (SELECT MAX(ID_Proyecto) FROM PROYECTO), 5);

-- 5.3. Prueba de Restricción CHECK en la tabla FASE.
-- Intento de inserción de un estado no válido ('Dudoso') fuera del dominio permitido.
-- Se espera un error de violación de restricción check.
INSERT INTO FASE (ID_Proyecto, Num_Fase, Nombre_Fase, Estado) 
VALUES ((SELECT MAX(ID_Proyecto) FROM PROYECTO), 1, 'Fase Test', 'Dudoso');

-- 5.4. REVERSIÓN (Limpieza):
-- Eliminación del proyecto de prueba y sus dependencias (Cascade delete en FASE).
DELETE FROM TRABAJA_EN WHERE ID_Proyecto = (SELECT MAX(ID_Proyecto) FROM PROYECTO WHERE Nombre_Descriptivo = 'Proyecto Test de Integridad');
DELETE FROM PROYECTO WHERE Nombre_Descriptivo = 'Proyecto Test de Integridad';


-- -----------------------------------------------------------------------------------
-- BLOQUE 6: DISPARADOR DE STOCK (Tabla: SUMINISTRA)
-- Objetivo: Verificación de la lógica de negocio (Trigger) para actualización automática.
-- -----------------------------------------------------------------------------------

-- 6.1. Consulta del stock inicial de la referencia 'GME123'.
SELECT Ref_Pieza, Stock_Actual FROM PIEZA WHERE Ref_Pieza = 'GME123';

-- 6.2. Simulación de compra: Inserción en la relación ternaria SUMINISTRA (+10 unidades).
INSERT INTO SUMINISTRA (CIF_Proveedor, Ref_Pieza, ID_Proyecto, Precio_Compra, Fecha_Suministro, Cantidad) 
VALUES ('B12345678', 'GME123', 1, 15.00, CURRENT_DATE, 10);

-- 6.3. Verificación del stock final.
-- El valor debe haberse incrementado en 10 unidades automáticamente.
SELECT Ref_Pieza, Stock_Actual FROM PIEZA WHERE Ref_Pieza = 'GME123';

-- 6.4. REVERSIÓN (Limpieza):
-- Eliminación del registro de suministro.
DELETE FROM SUMINISTRA WHERE Ref_Pieza = 'GME123' AND Cantidad = 10 AND Fecha_Suministro = CURRENT_DATE;
-- Corrección manual del stock para restaurar el estado original.
UPDATE PIEZA SET Stock_Actual = Stock_Actual - 10 WHERE Ref_Pieza = 'GME123';


-- -----------------------------------------------------------------------------------
-- BLOQUE 7: DISPARADOR DE EXCLUSIÓN (Tabla: ASISTE_A)
-- Objetivo: Validar la restricción de exclusividad entre Taller y Rodaje.
-- -----------------------------------------------------------------------------------

-- 7.1. Confirmación de que el vehículo 'SALLHV123456' tiene un proyecto activo.
SELECT ID_Proyecto, VIN_Vehiculo, Fecha_Fin FROM PROYECTO WHERE VIN_Vehiculo = 'SALLHV123456';

-- 7.2. Intento de asignación a un Rodaje.
-- Se espera una excepción lanzada por el disparador impidiendo la operación.
INSERT INTO ASISTE_A (VIN, ID_Rodaje, Fecha_Inicio, Fecha_Fin, Coste_Alquiler) 
VALUES ('SALLHV123456', 1, CURRENT_DATE, CURRENT_DATE + 5, 5000);

-- No requiere reversión ya que la operación es abortada por el sistema.