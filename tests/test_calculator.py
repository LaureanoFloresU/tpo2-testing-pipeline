import pytest

from descuentos import calcular_precio_final


def test_cliente_premium_recibe_descuento_exitoso():
    assert calcular_precio_final(10000, "premium") == 9000


def test_monto_negativo_genera_error():
    with pytest.raises(ValueError, match="monto no puede ser negativo"):
        calcular_precio_final(-1, "regular")


def test_compra_en_limite_recibe_descuento_adicional():
    assert calcular_precio_final(100000, "vip") == 75000


def test_tipo_cliente_desconocido_genera_error():
    with pytest.raises(ValueError, match="Tipo de cliente no valido"):
        calcular_precio_final(5000, "estudiante")

