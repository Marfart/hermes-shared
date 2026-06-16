# Nmap Live Scan — Real-World Example (2026-06-08)

## Environment

| Field | Value |
|-------|-------|
| Local machine | 192.168.1.93 (Dell, Biostar H510MHP) |
| Gateway | 192.168.1.1 (88:81:B9:4F:12:C2) |
| Subnet | 192.168.1.0/24 |
| Nmap version | 7.80 (32-bit Windows) |
| NSE scripts | 599 available |

## Phase 1: Host Discovery

```bash
nmap -sn 192.168.1.0/24
```

**Result:** 88 live hosts out of 256 IPs (34% occupancy rate). Took ~9 seconds.

This reveals:
- Active device density
- Which sub-ranges are populated
- Whether the network is office vs residential (88 hosts on a /24 is typical office)

## Phase 2: Gateway Reconnaissance

```bash
nmap -sV -O -T4 -p 1-1000,3389,8080,8443,5000,8000 192.168.1.1
```

**Result:**
| Port | State | Service | Notes |
|------|-------|---------|-------|
| 53/tcp | open | DNS (tcpwrapped) | |
| 80/tcp | open | HTTP | Web admin interface |
| 443/tcp | open | HTTPS | Secure web admin |

HTTP response headers revealed:
- `X-Frame-Options: SAMEORIGIN`
- `X-XSS-Protection: 1; mode=block`
- `Content-Security-Policy: default-src 'self'`
- 405 on OPTIONS requests → locked-down router firmware

**MAC:** 88:81:B9:4F:12:C2 (unknown brand — not in nmap OUI DB)

## Phase 3: Interesting Host Deep Scan

### Target Selection

Pick hosts whose MAC OUI suggests a workgroup/personal machine (not IoT/embedded). Scan only common attack surfaces first:

```bash
nmap -sV -p 22,80,443,135,139,445,3389,8080 TARGET_IP
```

### Find: MSI Workstation (.114) — Most Vulnerable

```bash
nmap -sV -O -T4 -p- --min-rate=5000 192.168.1.114
```

**OS:** Windows Server 2008 R2 - 2012 (end of life since January 2020)

**Open ports (summary):**
| Port | Service | Version | Risk |
|------|---------|---------|------|
| 80 | HTTP | IIS 7.5 | 🔴 Old |
| 445 | SMB | Server 2008 R2 | 🔴 **EternalBlue (MS17-010) possible** |
| 1433 | **MS SQL** | SQL Server 2008 R2 | 🔴 **EOL, known vulns** |
| 3389 | RDP | Windows RDP | 🟡 Open to LAN |
| 8443 | HTTPS | Apache (VisualSVN Server) | 🔴 **Source code repo!** |
| 8020 | HTTP | Microsoft HTTPAPI | 🟡 |
| 135/139 | MSRPC/NetBIOS | Windows | 🟡 |
| 82xx-83xx | Unknown | Multiple services | ? |
| 49152-49247 | MSRPC | Dynamic RPC ports | Normal |

**VisualSVN Server** on port 8443 requires auth (401 Unauthorized with `Basic realm="VisualSVN Server"`).

### Find: Intel Corporate (.115) — SMB Exposed

```bash
nmap -sV -p 135,139,445,3389 192.168.1.115
```

| Port | Service | Detail |
|------|---------|--------|
| 135 | MSRPC | Open |
| 139 | NetBIOS | Open |
| 445 | SMB | Windows 7-10, WorkGroup |
| Hostname | XTZJ-20241223OU | |

### Find: Colorful (.51) — Windows SMB

```bash
nmap -sV -p 135,139,445,3389 192.168.1.51
```

Windows OS with SMB (135/139/445) open. Likely a desktop workstation.

### Virtual Machines Found

| IP | Type | MAC |
|----|------|-----|
| .41 | VirtualBox | Oracle |
| .124 | VMware | VMware |
| .223 | VMware | VMware |
| .230 | VMware | VMware |
| .235 | VirtualBox | Oracle |

## Command Reference

```bash
# Fast host discovery
nmap -sn 192.168.1.0/24

# Quick service scan on common ports
nmap -sV -p 22,80,443,135,139,445,3389,8080,8443 TARGET

# Deep scan: OS + version + all ports
nmap -sV -O -T4 -p- --min-rate=5000 TARGET

# Vulnerability scan with NSE
nmap --script vuln TARGET

# SMB enumeration
nmap --script smb-os-discovery TARGET
nmap --script smb-vuln-ms17-010 TARGET

# HTTP enumeration
nmap --script http-title,http-headers,http-methods TARGET

# Web directory brute-force (using gobuster equivalent NSE)
nmap --script http-enum TARGET

# Cross-check with browser
curl --noproxy "*" -s -I http://TARGET:80/
curl --noproxy "*" -s -I https://TARGET:8443/ --insecure
```

## Practical Methodology

### Step 1: Snapshot the network
```bash
nmap -sn SUBNET/CIDR -oA network_snapshot
```
Wait for completion (~10s for /24), analyze the MAC OUIs to identify:
- **Routers** (.1 or .254 typically)
- **Workstations** (Intel/ASUS/MSI/Colorful/Biostar)
- **Servers** (Intel, HP, Dell MACs)
- **VMs** (VMware/VirtualBox MACs)
- **IoT/Embedded** (Realtek, Positron, Espressif)

### Step 2: Prioritize targets
1. First: Gateway/router — understand the perimeter
2. Second: Any host running Server OS (2008 R2 / 2012 / 2016)
3. Third: VMs (often less patched)  
4. Fourth: Workstations with unusual ports open

### Step 3: Deep scan high-value targets
Run service version detection + OS fingerprinting on non-standard ports. The key is finding:
- **End-of-life software** (Server 2008 R2, SQL 2008 R2, IIS 7.5)
- **Source control servers** (VisualSVN, GitLab, GitHub Enterprise)
- **Database servers** (MS SQL on 1433, MySQL on 3306)
- **Remote access** (RDP 3389, SSH 22, VNC 5900)

### Step 4: Cross-verify with application-layer probes
Nmap can identify open ports but can't tell you what's behind the service:
```bash
curl --noproxy "*" -s -I http://TARGET:8080/   # Check HTTP response
curl --noproxy "*" -s -I https://TARGET:8443/ --insecure  # Check HTTPS
```

In our scan, this revealed that port 8443 was **VisualSVN Server** (an SVN source control server), not a generic HTTPS service — a finding Nmap alone couldn't identify.

## What This Revealed About the Network

- **88 devices** on a single /24 — high density, likely office/campus
- **One critical vulnerability**: Windows Server 2008 R2 (EOL 2020) with SMB + MS SQL + RDP exposed
- **Source code repository**: VisualSVN Server on the same vulnerable machine
- **Multiple virtualization platforms**: 2x VirtualBox + 3x VMware
- **SMB exposure**: 6+ hosts with ports 135/139/445 open
- **No obvious security controls**: No NIDS/NIPS detection, no port knocking, standard Windows firewall

## See Also

- `wifi-cracking-comprehensive.md` — WiFi attack modes, hardware, command chains
