from descuentos import calcular_precio_final


def main() -> None:
    monto = float(input("Ingrese el monto de la compra: "))
    tipo_cliente = input("Ingrese el tipo de cliente (regular, premium, vip): ")
    precio_final = calcular_precio_final(monto, tipo_cliente)
    print(f"Precio final: ${precio_final:.2f}")


if __name__ == "__main__":
    main()

