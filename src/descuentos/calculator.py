"""Logica de negocio para calcular descuentos."""


DESCUENTOS_POR_CLIENTE = {
    "regular": 0.0,
    "premium": 0.10,
    "vip": 0.20,
}


def calcular_precio_final(monto: float, tipo_cliente: str) -> float:
    """Calcula el precio final aplicando el descuento correspondiente.

    Reglas:
    - Clientes regular: sin descuento.
    - Clientes premium: 10% de descuento.
    - Clientes vip: 20% de descuento.
    - Compras desde 100000 reciben un 5% adicional.
    """
    if monto < 0:
        raise ValueError("El monto no puede ser negativo")

    cliente_normalizado = tipo_cliente.strip().lower()
    if cliente_normalizado not in DESCUENTOS_POR_CLIENTE:
        raise ValueError("Tipo de cliente no valido")

    descuento = DESCUENTOS_POR_CLIENTE[cliente_normalizado]
    if monto >= 100000:
        descuento += 0.05

    precio_final = monto * (1 - descuento)
    return round(precio_final, 2)

