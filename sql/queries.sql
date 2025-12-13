-- CONSULTAS DE PRUEBA - PROYECTO HERITAGE ROVER WORKS

-- 1. Listado detallado de proyectos (JOIN entre 4 tablas)
SELECT 
    C.Nombre || ' ' || C.Apellidos AS Cliente,
    V.Matricula,
    P.Nombre_Descriptivo AS Proyecto,
    E.Nombre || ' ' || E.Apellidos AS Supervisor
FROM PROYECTO P
JOIN VEHICULO V ON P.VIN_Vehiculo = V.VIN
JOIN CLIENTE CL ON V.DNI_Propietario = CL.DNI_Cliente
JOIN PERSONA C ON CL.DNI_Cliente = C.DNI
JOIN EMPLEADO EMP ON P.DNI_Supervisor = EMP.DNI_Empleado
JOIN PERSONA E ON EMP.DNI_Empleado = E.DNI;

-- 2. Coste total de piezas por Proyecto (Agregación SUM y GROUP BY)
SELECT 
    P.Nombre_Descriptivo,
    COUNT(S.Ref_Pieza) AS Num_Piezas_Compradas,
    COALESCE(SUM(S.Precio_Compra * S.Cantidad), 0) AS Coste_Total_Piezas
FROM PROYECTO P
LEFT JOIN SUMINISTRA S ON P.ID_Proyecto = S.ID_Proyecto
GROUP BY P.ID_Proyecto, P.Nombre_Descriptivo;

-- 3. Buscar piezas compatibles con Defender (Relación M:N)
SELECT 
    M.Nombre_Comercial AS Modelo,
    P.Nombre AS Pieza_Compatible,
    P.Stock_Actual
FROM MODELO_CATALOGO M
JOIN COMPATIBILIDAD C ON M.ID_Modelo = C.ID_Modelo
JOIN PIEZA P ON C.Ref_Pieza = P.Ref_Pieza
WHERE M.Nombre_Comercial LIKE '%Defender%';