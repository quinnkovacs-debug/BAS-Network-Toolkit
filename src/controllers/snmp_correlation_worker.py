"""Background worker for SNMP switch-port correlation."""

import asyncio

from PySide6.QtCore import QObject, Signal, Slot

from src.models.network_device import NetworkDevice
from src.network.snmp.client import (
    SnmpQueryError,
    query_identity,
    query_mac_table,
)
from src.network.snmp.correlation import (
    build_mac_port_lookup,
    enrich_device_with_switch_info,
)


class SnmpCorrelationWorker(QObject):
    """Correlate discovered devices with switch ports using SNMPv2c."""

    device_enriched = Signal(object)

    completed = Signal(int, int)
    failed = Signal(str)
    finished = Signal()

    def __init__(
        self,
        devices: list[NetworkDevice],
        switch_ip: str,
        community: str,
        vlan_id: int,
    ) -> None:
        super().__init__()

        # Copy the list so this worker has its own stable collection.
        self.devices = list(devices)

        self.switch_ip = switch_ip
        self.community = community
        self.vlan_id = vlan_id

    @Slot()
    def run(self) -> None:
        """Run the asynchronous SNMP work inside this worker thread."""

        try:
            asyncio.run(self._correlate())

        except (SnmpQueryError, ValueError) as error:
            message = str(error) or repr(error)
            print(f"SNMP correlation error: {message}")
            self.failed.emit(message)

        except Exception as error:
            message = str(error) or repr(error)
            print(
                f"Unexpected SNMP correlation error: "
                f"{type(error).__name__}: {message}"
            )
            self.failed.emit(
                f"{type(error).__name__}: {message}"
            )

        finally:
            self.finished.emit()

    async def _correlate(self) -> None:
        """Query the switch once and enrich discovered devices."""

        identity = await query_identity(
            host=self.switch_ip,
            community=self.community,
            timeout=10.0,
            retries=3,
        )

        switch_name = identity.get(
            "SNMPv2-SMI::mib-2.1.5.0",
            self.switch_ip,
        )

        entries = await query_mac_table(
            host=self.switch_ip,
            community=self.community,
            vlan_id=self.vlan_id,
            timeout=10.0,
            retries=3,
        )

        lookup = build_mac_port_lookup(
            switch_name=switch_name,
            switch_ip=self.switch_ip,
            entries=entries,
        )

        matched_count = 0

        for device in self.devices:
            matched = enrich_device_with_switch_info(
                device=device,
                lookup=lookup,
            )

            if not matched:
                continue

            matched_count += 1
            self.device_enriched.emit(device)

        self.completed.emit(
            matched_count,
            len(self.devices),
        )