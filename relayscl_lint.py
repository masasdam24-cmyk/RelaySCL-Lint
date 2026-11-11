#!/usr/bin/env python3
"""RelaySCL-Lint: focused, offline IEC 61850 SCL/GOOSE consistency checks.

This is a heuristic consistency checker, NOT a full IEC 61850 schema validator.
Only the Python standard library is required.
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

VERSION = "0.1.0"
MAX_FILE_BYTES = 20 * 1024 * 1024
HEX4 = re.compile(r"^[0-9A-Fa-f]{4}$")
MAC = re.compile(r"^([0-9A-Fa-f]{2})([-:])(?:[0-9A-Fa-f]{2}\2){4}[0-9A-Fa-f]{2}$")


def name(element: ET.Element) -> str:
    return element.tag.rsplit("}", 1)[-1]


def children(element: ET.Element, tag: str) -> list[ET.Element]:
    return [node for node in element if name(node) == tag]


def child(element: ET.Element, tag: str) -> ET.Element | None:
    return next((node for node in element if name(node) == tag), None)


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    location: str
    message: str


class Scanner:
    def __init__(self) -> None:
        self.findings: list[Finding] = []

    def add(self, severity: str, code: str, loc: str, message: str) -> None:
        self.findings.append(Finding(severity, code, loc, message))

    def scan(self, root: ET.Element) -> list[Finding]:
        if name(root) != "SCL":
            self.add("error", "SCL001", "/", "Root element must be SCL.")
            return self.findings

        # (IED name, access point, logical device inst, GSEControl name)
        controls: dict[tuple[str, str, str, str], str] = {}
        ieds: set[str] = set()
        for ied in children(root, "IED"):
            ied_name = ied.get("name", "")
            ied_loc = f"IED[{ied_name or '?'}]"
            if not ied_name:
                self.add("error", "SCL010", ied_loc, "IED has no name.")
            elif ied_name in ieds:
                self.add("error", "SCL011", ied_loc, "Duplicate IED name.")
            ieds.add(ied_name)
            for ap in children(ied, "AccessPoint"):
                ap_name = ap.get("name", "")
                server = child(ap, "Server")
                if server is None:
                    continue
                for ld in children(server, "LDevice"):
                    ld_inst = ld.get("inst", "")
                    ln0 = child(ld, "LN0")
                    if ln0 is None:
                        continue
                    loc = f"{ied_loc}/AccessPoint[{ap_name}]/LDevice[{ld_inst}]/LN0"
                    datasets = set()
                    for ds in children(ln0, "DataSet"):
                        ds_name = ds.get("name", "")
                        if ds_name in datasets:
                            self.add("error", "GSE006", loc, f"Duplicate DataSet name '{ds_name}'.")
                        datasets.add(ds_name)
                        if not children(ds, "FCDA"):
                            self.add("warning", "GSE007", loc, f"DataSet '{ds_name}' has no FCDA entries.")
                    cb_names = set()
                    for cb in children(ln0, "GSEControl"):
                        cb_name = cb.get("name", "")
                        cb_loc = f"{loc}/GSEControl[{cb_name or '?'}]"
                        if not cb_name:
                            self.add("error", "GSE001", cb_loc, "GSEControl name is empty.")
                        if cb_name in cb_names:
                            self.add("error", "GSE002", cb_loc, "Duplicate GSEControl name in LN0.")
                        cb_names.add(cb_name)
                        key = (ied_name, ap_name, ld_inst, cb_name)
                        controls[key] = cb_loc
                        data_set = cb.get("datSet", "")
                        if not data_set:
                            self.add("error", "GSE003", cb_loc, "GSEControl has no datSet reference.")
                        elif data_set not in datasets:
                            self.add("error", "GSE004", cb_loc, f"Referenced DataSet '{data_set}' not found in the same LN0.")
                        rev = cb.get("confRev", "")
                        if not rev.isdigit() or int(rev) < 1:
                            self.add("warning", "GSE005", cb_loc, "confRev should be a positive integer; review versioning.")

        # Communication is allowed to be absent in partial ICD files.
        communication = child(root, "Communication")
        if communication is None:
            if controls:
                self.add("info", "COM001", "/SCL", "Communication absent; GOOSE network addresses cannot be checked.")
            return self.findings

        mapped: set[tuple[str, str, str, str]] = set()
        for subnet in children(communication, "SubNetwork"):
            subnet_name = subnet.get("name", "")
            for cap in children(subnet, "ConnectedAP"):
                ied_name = cap.get("iedName", "")
                ap_name = cap.get("apName", "")
                for gse in children(cap, "GSE"):
                    ld_inst = gse.get("ldInst", "")
                    cb_name = gse.get("cbName", "")
                    gse_loc = (f"Communication/SubNetwork[{subnet_name}]/"
                               f"ConnectedAP[{ied_name}/{ap_name}]/GSE[{ld_inst}/{cb_name}]")
                    key = (ied_name, ap_name, ld_inst, cb_name)
                    if key not in controls:
                        self.add("warning", "COM002", gse_loc, "GSE network entry has no matching GSEControl in this file.")
                    if key in mapped:
                        self.add("warning", "COM003", gse_loc, "Duplicate GSE mapping for the same control block.")
                    mapped.add(key)
                    address = child(gse, "Address")
                    if address is None:
                        self.add("warning", "COM004", gse_loc, "GSE network entry has no Address element.")
                        continue
                    values: dict[str, str] = {}
                    for p in children(address, "P"):
                        typ = p.get("type", "").upper()
                        if typ in values:
                            self.add("warning", "COM005", gse_loc, f"Duplicate address parameter '{typ}'.")
                        values[typ] = (p.text or "").strip()
                    mac = values.get("MAC-ADDRESS")
                    if mac is None:
                        self.add("warning", "COM006", gse_loc, "Missing GOOSE MAC-Address.")
                    else:
                        match = MAC.fullmatch(mac)
                        if not match:
                            self.add("error", "COM007", gse_loc, f"Malformed MAC-Address '{mac}'.")
                        elif not (int(match.group(1), 16) & 1):
                            self.add("warning", "COM008", gse_loc, "MAC-Address is not a multicast address.")
                    appid = values.get("APPID")
                    if appid is None:
                        self.add("warning", "COM009", gse_loc, "Missing GOOSE APPID network parameter.")
                    elif not HEX4.fullmatch(appid):
                        self.add("error", "COM010", gse_loc, "APPID should contain four hexadecimal digits.")
                    vlan = values.get("VLAN-ID")
                    if vlan is not None:
                        if not re.fullmatch(r"[0-9a-fA-F]{1,3}", vlan) or int(vlan, 16) > 4094:
                            self.add("error", "COM011", gse_loc, "VLAN-ID is not a valid 0..4094 hexadecimal value.")
                        elif len(vlan) != 3:
                            self.add("info", "COM012", gse_loc, "VLAN-ID is valid but not in the common 3-digit SCL form.")
                    priority = values.get("VLAN-PRIORITY")
                    if priority is not None and (not priority.isdigit() or int(priority) > 7):
                        self.add("error", "COM013", gse_loc, "VLAN-PRIORITY must be an integer from 0 to 7.")
        for key, loc in controls.items():
            if key not in mapped:
                self.add("info", "COM014", loc, "No GSE Communication mapping found in this file.")
        return self.findings


def scan_xml(source: bytes) -> list[Finding]:
    scanner = Scanner()
    if len(source) > MAX_FILE_BYTES:
        scanner.add("error", "XML003", "/", "File exceeds the 20 MiB safety limit.")
        return scanner.findings
    try:
        root = ET.fromstring(source)
    except ET.ParseError as exc:
        scanner.add("error", "XML001", "/", f"Malformed XML: {exc}")
        return scanner.findings
    return scanner.scan(root)


def scan_file(path: Path) -> list[Finding]:
    try:
        if path.stat().st_size > MAX_FILE_BYTES:
            return [Finding("error", "XML003", "/", "File exceeds the 20 MiB safety limit.")]
        return scan_xml(path.read_bytes())
    except OSError as exc:
        return [Finding("error", "IO001", "/", f"Cannot read file: {exc}")]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Offline IEC 61850 SCL / GOOSE consistency checker")
    parser.add_argument("files", nargs="+", type=Path, help="SCL files (.scd, .cid, .icd or .xml)")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--strict", action="store_true", help="Warnings also cause nonzero exit status")
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    args = parser.parse_args(argv)
    reports = []
    total = Counter()
    for path in args.files:
        findings = scan_file(path)
        summary = Counter(f.severity for f in findings)
        total.update(summary)
        reports.append({"file": str(path), "findings": [asdict(f) for f in findings],
                        "summary": {k: summary[k] for k in ("error", "warning", "info")}})
    if args.format == "json":
        print(json.dumps({"tool": "RelaySCL-Lint", "version": VERSION, "reports": reports}, indent=2, ensure_ascii=False))
    else:
        for report in reports:
            print(f"{report['file']}:")
            for f in report["findings"]:
                print(f"  [{f['severity'].upper()}] {f['code']} {f['location']} — {f['message']}")
            if not report["findings"]:
                print("  No findings from the implemented checks.")
            print(f"  errors={report['summary']['error']} warnings={report['summary']['warning']} info={report['summary']['info']}")
    return 1 if total["error"] or (args.strict and total["warning"]) else 0


if __name__ == "__main__":
    sys.exit(main())
