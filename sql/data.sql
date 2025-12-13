-- Vaciamos tablas por si acaso (orden inverso para respetar FKs)
TRUNCATE TABLE SUMINISTRA, ASISTE_A, TRABAJA_EN, COMPATIBILIDAD, FASE, PROYECTO, VEHICULO, EMPLEADO, CLIENTE, PERSONA, RODAJE, MODELO_CATALOGO, PROVEEDOR, PIEZA RESTART IDENTITY CASCADE;

-- --------------------------------------------------------
-- 1. CARGA DE TABLAS MAESTRAS
-- --------------------------------------------------------

-- PERSONAS (Base para Clientes y Empleados)
INSERT INTO PERSONA (DNI, Nombre, Apellidos, Email, Telefono) VALUES
('11111111A', 'Carlos', 'Sainz', 'carlos@mail.com', '600111222'), -- Cliente
('22222222B', 'Fernando', 'Alonso', 'nano@mail.com', '600333444'), -- Cliente
('33333333C', 'Marc', 'Coma', 'marc@taller.com', '600555666'),   -- Empleado (Mecánico)
('44444444D', 'Laia', 'Sanz', 'laia@taller.com', '600777888'),   -- Empleado (Jefa Taller)
('55555555E', 'Pedro', 'Martinez', 'pedro@cine.com', '600999000'); -- Cliente

-- MODELOS DE CATÁLOGO (Land Rovers Clásicos)
INSERT INTO MODELO_CATALOGO (Nombre_Comercial) VALUES
('Land Rover Series I 80"'),
('Land Rover Series IIA 88"'),
('Land Rover Series III 109"'),
('Land Rover Santana 88 Especial'),
('Defender 90 Tdi'),
('Defender 110 V8');

-- PIEZAS (Recambios reales)
INSERT INTO PIEZA (Ref_Pieza, Nombre, Descripcion, Stock_Actual) VALUES
('RTC3429', 'Motor de Arranque Lucas', 'Original Lucas 12V', 5),
('GME123', 'Filtro Aceite', 'Compatible Tdi y Gasolina', 50),
('FRC456', 'Caja de Cambios LT77', 'Reconstruida', 2),
('BPM789', 'Kit Suspensión Parabólica', 'Para Series II y III', 4),
('EXT001', 'Cabrestante Warn 8274', 'Accesorio Offroad', 1);

-- PROVEEDORES
INSERT INTO PROVEEDOR (CIF, Nombre_Empresa, Web) VALUES
('B12345678', 'Britpart UK', 'www.britpart.com'),
('B87654321', 'Bearmach', 'www.bearmach.com'),
('B11223344', 'Recambios Juanito', 'www.juanito4x4.es');

-- RODAJES (Películas)
INSERT INTO RODAJE (Productora, Lugar) VALUES
('Netflix España', 'Desierto de Tabernas'),
('BBC Documentaries', 'Picos de Europa');

-- --------------------------------------------------------
-- 2. CARGA DE JERARQUÍA (IS_A)
-- --------------------------------------------------------

-- CLIENTES (Carlos, Fernando, Pedro)
INSERT INTO CLIENTE (DNI_Cliente, Num_Cuenta, Fecha_Alta) VALUES
('11111111A', 'ES99000011112222', '2020-01-15'),
('22222222B', 'ES99000033334444', '2021-05-20'),
('55555555E', 'ES99000055556666', '2022-11-30');

-- EMPLEADOS (Marc, Laia)
INSERT INTO EMPLEADO (DNI_Empleado, NSS, Salario, Fecha_Contratacion) VALUES
('33333333C', '281234567890', 1800.50, '2019-02-01'), -- Marc
('44444444D', '280987654321', 2500.00, '2018-06-15'); -- Laia

-- --------------------------------------------------------
-- 3. VEHÍCULOS (Relación 1:N)
-- --------------------------------------------------------

INSERT INTO VEHICULO (VIN, Matricula, Anio, Color_Original, Tipo_Motor, DNI_Propietario) VALUES
('SALLHV123456', 'M-1234-OP', 1978, 'Verde Inglés', '2.25 Diesel', '11111111A'), -- Coche de Carlos
('SALLHV654321', 'B-4321-KZ', 1985, 'Arena', '3.5 V8', '22222222B'),        -- Coche de Fernando
('SANTANA99999', 'TF-5678-AD', 1982, 'Azul Marino', '2.25 Gasolina', '11111111A'); -- Otro de Carlos

-- --------------------------------------------------------
-- 4. PROYECTOS Y FASES (Entidad Débil)
-- --------------------------------------------------------

-- PROYECTO 1: Restauración del coche de Carlos
INSERT INTO PROYECTO (Nombre_Descriptivo, Fecha_Inicio, VIN_Vehiculo, DNI_Supervisor) 
VALUES ('Restauración Motor y Pintura', '2023-01-10', 'SALLHV123456', '44444444D'); 
-- Laia (4444D) es la jefa del proyecto 1

-- PROYECTO 2: Revisión frenos coche de Fernando
INSERT INTO PROYECTO (Nombre_Descriptivo, Fecha_Inicio, VIN_Vehiculo, DNI_Supervisor) 
VALUES ('Revisión Sistema Frenos', '2023-02-15', 'SALLHV654321', '33333333C');
-- Marc (3333C) es el jefe del proyecto 2

-- FASES (Entidad Débil - Dependen del ID del proyecto, asumimos ID 1 y 2)
-- Fases para Proyecto 1
INSERT INTO FASE (ID_Proyecto, Num_Fase, Nombre_Fase, Estado) VALUES
(1, 1, 'Desmontaje Motor', 'Terminado'),
(1, 2, 'Rectificado Culata', 'En Proceso'),
(1, 3, 'Pintura Carrocería', 'Pendiente');

-- Fases para Proyecto 2
INSERT INTO FASE (ID_Proyecto, Num_Fase, Nombre_Fase, Estado) VALUES
(2, 1, 'Revisión Discos', 'Terminado'),
(2, 2, 'Cambio Pastillas', 'Terminado');

-- --------------------------------------------------------
-- 5. RELACIONES M:N Y TERNARIAS
-- --------------------------------------------------------

-- TRABAJA_EN (Inclusividad: El jefe debe trabajar en el proyecto)
INSERT INTO TRABAJA_EN (DNI_Empleado, ID_Proyecto, Horas_Dedicadas) VALUES
('44444444D', 1, 10), -- Laia trabaja en Proy 1 (Es Jefa, CUMPLE INCLUSIVIDAD)
('33333333C', 1, 40), -- Marc trabaja en Proy 1 (Mecánico)
('33333333C', 2, 5);  -- Marc trabaja en Proy 2 (Es Jefe, CUMPLE INCLUSIVIDAD)

-- COMPATIBILIDAD (Qué piezas valen para qué coches)
INSERT INTO COMPATIBILIDAD (Ref_Pieza, ID_Modelo) VALUES
('RTC3429', 1), -- Arranque vale para Series I
('RTC3429', 2), -- Arranque vale para Series II
('GME123', 5),  -- Filtro vale para Defender
('GME123', 6);  -- Filtro vale para Defender V8

-- SUMINISTRA (Ternaria: Quién vendió qué para qué proyecto)
INSERT INTO SUMINISTRA (CIF_Proveedor, Ref_Pieza, ID_Proyecto, Precio_Compra, Fecha_Suministro, Cantidad) VALUES
('B12345678', 'RTC3429', 1, 150.00, '2023-01-12', 1), -- Britpart vendió arranque para Proyecto 1
('B87654321', 'GME123', 2, 12.50, '2023-02-16', 2);   -- Bearmach vendió filtros para Proyecto 2

-- ASISTE_A (Rodajes - Exclusión: Este coche NO puede tener proyecto abierto)
-- El coche SANTANA99999 no tiene proyectos activos, así que puede ir a rodaje.
INSERT INTO ASISTE_A (VIN, ID_Rodaje, Fecha_Inicio, Fecha_Fin, Coste_Alquiler) VALUES
('SANTANA99999', 1, '2023-06-01', '2023-06-30', 3000.00);