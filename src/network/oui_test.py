"""Standalone test for MAC manufacturer lookup."""

from src.network.oui_lookup import lookup_manufacturer


def main() -> None:
    mac_address = input("MAC address: ").strip()

    manufacturer = lookup_manufacturer(mac_address)

    if manufacturer:
        print(f"Manufacturer: {manufacturer}")
    else:
        print("Manufacturer not found.")


if __name__ == "__main__":
    main()