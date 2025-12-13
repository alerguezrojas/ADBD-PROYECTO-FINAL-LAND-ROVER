-- --------------------------------------------------------
-- TRIGGER A: ACTUALIZAR STOCK AUTOMÁTICAMENTE
-- --------------------------------------------------------

-- 1. Función
CREATE OR REPLACE FUNCTION actualizar_stock_compra()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE PIEZA
    SET Stock_Actual = Stock_Actual + NEW.Cantidad
    WHERE Ref_Pieza = NEW.Ref_Pieza;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 2. Trigger
DROP TRIGGER IF EXISTS TRG_Actualizar_Stock ON SUMINISTRA;
CREATE TRIGGER TRG_Actualizar_Stock
AFTER INSERT ON SUMINISTRA
FOR EACH ROW
EXECUTE FUNCTION actualizar_stock_compra();

-- --------------------------------------------------------
-- TRIGGER B: EXCLUSIÓN (TALLER VS RODAJE)
-- --------------------------------------------------------

-- 1. Función
CREATE OR REPLACE FUNCTION validar_exclusion_rodaje()
RETURNS TRIGGER AS $$
DECLARE
    proyectos_activos INT;
BEGIN
    -- Buscamos si el coche tiene proyectos sin terminar (Fecha_Fin es NULL)
    SELECT COUNT(*) INTO proyectos_activos
    FROM PROYECTO
    WHERE VIN_Vehiculo = NEW.VIN AND Fecha_Fin IS NULL;

    IF proyectos_activos > 0 THEN
        RAISE EXCEPTION 'ERROR DE EXCLUSIÓN: El vehículo % está en el taller y no puede ir a rodaje.', NEW.VIN;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 2. Trigger
DROP TRIGGER IF EXISTS TRG_Check_Exclusion_Rodaje ON ASISTE_A;
CREATE TRIGGER TRG_Check_Exclusion_Rodaje
BEFORE INSERT ON ASISTE_A
FOR EACH ROW
EXECUTE FUNCTION validar_exclusion_rodaje();