# BAS Network Toolkit Roadmap

## Vision

Build a professional Windows toolkit specifically for Building Automation System (BAS) technicians.

The goal is not to replace Wireshark, Nmap, Niagara Workbench, or vendor tools.

The goal is to eliminate the repetitive field tasks that technicians perform every day by combining the most useful functions into one fast, intuitive application.

---

# Current Status

## Version 0.2 (Current Development)

### Application Framework

- [x] GitHub project created
- [x] Python project structure
- [x] Virtual environment
- [x] PySide6 GUI
- [x] Modular project architecture
- [x] Adapter panel
- [x] Discovery panel
- [x] Background worker thread

### Network Adapter Discovery

- [x] Enumerate Windows adapters
- [x] Display adapter status
- [x] Display link speed
- [x] Display MAC address
- [x] Display interface index
- [x] Display IPv4 address
- [x] Display subnet mask
- [x] Display gateway
- [x] Display DHCP status
- [x] Display DNS servers
- [x] Preferred adapter selection

### LLDP Discovery

- [x] Npcap interface mapping
- [x] Capture LLDP packets
- [x] Parse LLDP TLVs
- [x] Display:

  - Switch Name
  - Switch Port
  - Port Description
  - Management IP
  - Native VLAN
  - Source MAC
  - System Description

- [x] Background packet capture
- [x] Discover button
- [x] Stop button
- [ ] Clean shutdown during active discovery

---

# Version 0.3

## User Experience

- [ ] Discovery timer
- [ ] Elapsed time display
- [ ] Improved status messages
- [ ] Activity log window
- [ ] Copy discovered information to clipboard
- [ ] Remember last selected adapter

## Discovery

- [ ] CDP parser
- [ ] Vendor detection
- [ ] Cisco platform parsing
- [ ] Aruba parsing
- [ ] HP / ArubaOS parsing
- [ ] Dell parsing

---

# Version 0.4

## BAS Quick Scan

Perform a rapid scan of the local BAS network.

### Discovery

- [ ] Gateway detection
- [ ] Switch detection
- [ ] BACnet devices
- [ ] Modbus TCP devices
- [ ] Niagara stations
- [ ] Schneider controllers
- [ ] Distech controllers

### Quick TCP Tests

- [ ] HTTPS (443)
- [ ] HTTP (80)
- [ ] SSH (22)
- [ ] BACnet/IP
- [ ] Modbus TCP
- [ ] Niagara FOX
- [ ] SNMP

---

# Version 0.5

## BACnet Discovery

- [ ] Who-Is scanner
- [ ] I-Am parser
- [ ] Device Instance
- [ ] Vendor ID
- [ ] Vendor Name
- [ ] Max APDU
- [ ] Segmentation
- [ ] BACnet port scanning (47808+)

---

# Version 0.6

## Web Interface Detection

For discovered devices:

- [ ] Test HTTPS
- [ ] Test HTTP
- [ ] Detect available web interface
- [ ] Open Web Interface button
- [ ] Copy URL
- [ ] Open Management IP

---

# Version 0.7

## Device Intelligence

Automatically recognize common BAS equipment.

Examples:

- Tridium JACE
- Schneider AS-P
- Schneider RP-C
- Schneider MP Series
- Distech ECY
- Distech ECB
- Contemporary Controls
- Cisco Catalyst
- Aruba
- Dell Networking

Display friendly names instead of only ports.

---

# Version 0.8

## Reporting

- [ ] Export to clipboard
- [ ] Export CSV
- [ ] Export PDF
- [ ] Discovery history
- [ ] Save session

---

# Version 0.9

## Tools

- [ ] Ping utility
- [ ] DNS lookup
- [ ] MAC vendor lookup
- [ ] IP calculator
- [ ] Subnet calculator
- [ ] Port favorites

---

# Version 1.0

## BAS Field Toolkit

A polished field application suitable for everyday use.

### Included Tools

- Adapter Discovery
- LLDP Discovery
- CDP Discovery
- BACnet Discovery
- BAS Quick Scan
- Web Interface Launcher
- Ping Utility
- Port Tester
- Reporting

### Installer

- Windows installer
- Application icon
- Version information
- Settings
- Automatic update check
- Npcap detection
- Code signing

---

# Long-Term Ideas

## Niagara

- Station discovery
- FOX detection
- Platform detection
- Certificate viewer

## BACnet

- Object browser
- Read Property
- Write Property
- Trend viewer

## Modbus

- Register browser
- Register calculator
- Poll monitor

## Networking

- ARP table viewer
- LLDP neighbor history
- VLAN database
- Switch inventory

## Field Utilities

- QR code generation
- Cable labels
- Project notes
- Customer favorites
- Recently connected sites

---

# Design Principles

- One responsibility per module
- Responsive UI (never block the GUI thread)
- Build for technicians, not programmers
- Prefer protocol-aware discovery over generic port scanning
- Keep workflows fast (under 10 seconds whenever possible)
- Minimize typing in the field
- Make common tasks one-click operations
