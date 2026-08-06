"""Standalone test for the toolkit SNMP client."""

import asyncio
import getpass

from src.network.snmp.client import (
    SnmpQueryError,
    query_identity,
)


async def run_test() -> None:
    """Query one approved switch and print its identity."""

    switch_ip = input("Switch IP: ").strip()
    community = getpass.getpass("SNMP community: ")

    if not switch_ip:
        print("Switch IP cannot be empty.")
        return

    if not community:
        print("Community string cannot be empty.")
        return

    try:
        identity = await query_identity(
            host=switch_ip,
            community=community,
        )
    except SnmpQueryError as error:
        print(f"SNMP query failed: {error}")
        return

    print()
    print("Switch Identity")
    print("---------------")

    for name, value in identity.items():
        print(f"{name:<12}: {value}")


if __name__ == "__main__":
    asyncio.run(run_test())