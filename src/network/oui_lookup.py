"""Local MAC-address manufacturer lookup."""

from manuf import manuf


_parser = manuf.MacParser(update=False)


def lookup_manufacturer(mac_address: str) -> str:
    """Return the registered manufacturer for a MAC address.

    Returns an empty string if no manufacturer can be determined.
    """

    if not mac_address:
        return ""

    try:
        vendor = _parser.get_all(mac_address)
    except (ValueError, TypeError):
        return ""

    if vendor is None:
        return ""

    # Prefer the longer descriptive manufacturer name.
    if vendor.comment:
        return vendor.comment

    if vendor.manuf_long:
        return vendor.manuf_long

    if vendor.manuf:
        return vendor.manuf

    return ""