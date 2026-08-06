"""Read-only SNMPv2c queries used by the BAS Network Toolkit."""

from typing import Any

from pysnmp.hlapi.v1arch.asyncio import (
    CommunityData,
    ObjectIdentity,
    ObjectType,
    SnmpDispatcher,
    UdpTransportTarget,
    bulk_walk_cmd,  
    get_cmd,
)

import asyncio
from dataclasses import dataclass


SYSTEM_OBJECTS = {
    "sysDescr": "1.3.6.1.2.1.1.1.0",
    "sysObjectID": "1.3.6.1.2.1.1.2.0",
    "sysUpTime": "1.3.6.1.2.1.1.3.0",
    "sysContact": "1.3.6.1.2.1.1.4.0",
    "sysName": "1.3.6.1.2.1.1.5.0",
    "sysLocation": "1.3.6.1.2.1.1.6.0",
}


BRIDGE_PORT_IFINDEX = "1.3.6.1.2.1.17.1.4.1.2"
FDB_PORT = "1.3.6.1.2.1.17.4.3.1.2"
FDB_ENTRY_STATUS = "1.3.6.1.2.1.17.4.3.1.3"
IF_NAME = "1.3.6.1.2.1.31.1.1.1.1"


FDB_STATUS = {
    1: "other",
    2: "invalid",
    3: "learned",
    4: "self",
    5: "management",
}

@dataclass(slots=True)
class SwitchMacEntry:
    """One MAC-address entry learned by a managed switch."""

    mac_address: str
    vlan_id: int
    bridge_port: int
    interface_index: int | None
    interface_name: str
    status: str

class SnmpQueryError(RuntimeError):
    """A user-facing SNMP query failure."""


def oid_text(value: Any) -> str:
    """Return a numeric OID without a leading period."""

    return value.prettyPrint().lstrip(".")


def value_text(value: Any) -> str:
    """Convert a returned SNMP value to readable text."""

    return value.prettyPrint()


def error_message(
    error_indication: Any,
    error_status: Any,
    error_index: Any,
) -> str | None:
    """Return a readable SNMP error, or None when successful."""

    if error_indication:
        return str(error_indication)

    if error_status:
        position = int(error_index) if error_index else "unknown"

        return (
            f"{error_status.prettyPrint()} "
            f"at response position {position}"
        )

    return None


async def make_target(
    host: str,
    port: int,
    timeout: float,
    retries: int,
) -> UdpTransportTarget:
    """Create the SNMP UDP transport target."""

    return await UdpTransportTarget.create(
        (host, port),
        timeout=timeout,
        retries=retries,
    )


async def query_identity(
    host: str,
    community: str,
    port: int = 161,
    timeout: float = 3.0,
    retries: int = 1,
) -> dict[str, str]:
    """Read standard system identity information using SNMPv2c."""

    target = await make_target(
        host=host,
        port=port,
        timeout=timeout,
        retries=retries,
    )

    requests = [
        ObjectType(ObjectIdentity(oid))
        for oid in SYSTEM_OBJECTS.values()
    ]

    with SnmpDispatcher() as dispatcher:
        indication, status, index, var_binds = await get_cmd(
            dispatcher,
            CommunityData(community, mpModel=1),
            target,
            *requests,
            lookupMib=False,
        )

    failure = error_message(
        indication,
        status,
        index,
    )

    if failure:
        raise SnmpQueryError(failure)

    names_by_oid = {
        oid: name
        for name, oid in SYSTEM_OBJECTS.items()
    }

    return {
        names_by_oid.get(
            oid_text(name),
            oid_text(name),
        ): value_text(value)
        for name, value in var_binds
    }

async def walk_raw(
    host: str,
    community: str,
    base_oid: str,
    port: int = 161,
    timeout: float = 3.0,
    retries: int = 1,
) -> list[tuple[str, str]]:
    """Walk one SNMP subtree while preserving numeric OIDs."""

    target = await make_target(
        host=host,
        port=port,
        timeout=timeout,
        retries=retries,
    )

    values: list[tuple[str, str]] = []

    with SnmpDispatcher() as dispatcher:
        iterator = bulk_walk_cmd(
            dispatcher,
            CommunityData(community, mpModel=1),
            target,
            0,
            25,
            ObjectType(ObjectIdentity(base_oid)),
            lookupMib=False,
            lexicographicMode=False,
        )

        async for indication, status, error_index, var_binds in iterator:
            failure = error_message(
                indication,
                status,
                error_index,
            )

            if failure:
                raise SnmpQueryError(failure)

            values.extend(
                (
                    oid_text(name),
                    value_text(value),
                )
                for name, value in var_binds
            )

    return values

def normalize_mac(mac_address: str) -> str:
    """Normalize a MAC address to uppercase hyphenated form."""

    compact = "".join(
        character
        for character in mac_address.lower()
        if character in "0123456789abcdef"
    )

    if len(compact) != 12:
        raise ValueError(
            "MAC address must contain exactly 12 hexadecimal digits."
        )

    return "-".join(
        compact[index : index + 2].upper()
        for index in range(0, 12, 2)
    )


def mac_from_fdb_oid(
    oid: str,
    base_oid: str,
) -> str:
    """Extract a MAC address from a BRIDGE-MIB table OID."""

    prefix = base_oid.rstrip(".") + "."

    if not oid.startswith(prefix):
        raise SnmpQueryError(
            f"Unexpected forwarding-table OID: {oid}"
        )

    parts = oid[len(prefix) :].split(".")

    if len(parts) != 6:
        raise SnmpQueryError(
            f"Unexpected MAC index in OID: {oid}"
        )

    try:
        octets = [int(part) for part in parts]
    except ValueError as error:
        raise SnmpQueryError(
            f"Invalid MAC index in OID: {oid}"
        ) from error

    if any(octet < 0 or octet > 255 for octet in octets):
        raise SnmpQueryError(
            f"Invalid MAC octet in OID: {oid}"
        )

    return "-".join(
        f"{octet:02X}"
        for octet in octets
    )

async def query_mac_table(
    host: str,
    community: str,
    vlan_id: int,
    port: int = 161,
    timeout: float = 3.0,
    retries: int = 1,
) -> list[SwitchMacEntry]:
    """Read MAC, VLAN and interface correlations from one Cisco VLAN."""

    if not 1 <= vlan_id <= 4094:
        raise ValueError("VLAN ID must be between 1 and 4094.")

    # Cisco community-string indexing selects a VLAN-specific
    # BRIDGE-MIB instance.
    bridge_community = f"{community}@{vlan_id}"

    (
        fdb_ports,
        fdb_statuses,
        bridge_ports,
        interface_names,
    ) = await asyncio.gather(
        walk_raw(
            host=host,
            community=bridge_community,
            base_oid=FDB_PORT,
            port=port,
            timeout=timeout,
            retries=retries,
        ),
        walk_raw(
            host=host,
            community=bridge_community,
            base_oid=FDB_ENTRY_STATUS,
            port=port,
            timeout=timeout,
            retries=retries,
        ),
        walk_raw(
            host=host,
            community=bridge_community,
            base_oid=BRIDGE_PORT_IFINDEX,
            port=port,
            timeout=timeout,
            retries=retries,
        ),
        walk_raw(
            host=host,
            community=community,
            base_oid=IF_NAME,
            port=port,
            timeout=timeout,
            retries=retries,
        ),
    )

    status_by_mac = {
        mac_from_fdb_oid(oid, FDB_ENTRY_STATUS): int(value)
        for oid, value in fdb_statuses
        if value.isdigit()
    }

    if_index_by_bridge_port = {
        int(oid.rsplit(".", 1)[1]): int(value)
        for oid, value in bridge_ports
        if (
            oid.rsplit(".", 1)[1].isdigit()
            and value.isdigit()
        )
    }

    interface_name_by_index = {
        int(oid.rsplit(".", 1)[1]): value
        for oid, value in interface_names
        if oid.rsplit(".", 1)[1].isdigit()
    }

    entries: list[SwitchMacEntry] = []

    for oid, value in fdb_ports:
        if not value.isdigit():
            continue

        mac_address = mac_from_fdb_oid(
            oid,
            FDB_PORT,
        )

        status_number = status_by_mac.get(mac_address)

        # Status 2 means invalid or aged out.
        if status_number == 2:
            continue

        bridge_port = int(value)
        interface_index = if_index_by_bridge_port.get(
            bridge_port
        )

        interface_name = ""

        if interface_index is not None:
            interface_name = interface_name_by_index.get(
                interface_index,
                "",
            )

        entries.append(
            SwitchMacEntry(
                mac_address=mac_address,
                vlan_id=vlan_id,
                bridge_port=bridge_port,
                interface_index=interface_index,
                interface_name=interface_name,
                status=FDB_STATUS.get(
                    status_number,
                    str(status_number or ""),
                ),
            )
        )

    return sorted(
        entries,
        key=lambda entry: (
            entry.interface_name,
            entry.mac_address,
        ),
    )
