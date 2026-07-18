"""Best-effort local virtual machine detector.

This module tries to discover VMs on the host by querying common hypervisors:
- VirtualBox (VBoxManage)
- libvirt/virsh
- Hyper-V (PowerShell Get-VM)

The code is intentionally defensive: it will never raise when a command is missing
or fails — it simply returns an empty list or the VMs it could detect.
"""
from __future__ import annotations

import json
import platform
import shlex
import subprocess
from typing import Dict, List, Optional


def _run_cmd(cmd: List[str]) -> Optional[str]:
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL)
        return out.decode(errors="ignore")
    except Exception:
        return None


def detect_virtualbox() -> List[Dict]:
    out = _run_cmd(["VBoxManage", "list", "vms"]) or ""
    vms: List[Dict] = []
    for line in out.splitlines():
        # lines like: "\"name\" {uuid}"
        if not line.strip():
            continue
        parts = line.split()
        name = parts[0].strip('"')
        info = {"name": name, "hypervisor": "VirtualBox", "status": "unknown"}
        # try to get more info
        info_out = _run_cmd(["VBoxManage", "showvminfo", name, "--machinereadable"]) or ""
        for l in info_out.splitlines():
            if "VMState=" in l:
                info["status"] = l.split("=", 1)[1].strip().strip('"')
            if l.startswith("memory="):
                info["memory_mb"] = l.split("=", 1)[1].strip().strip('"')
            if l.startswith("cpus="):
                info["vcpus"] = l.split("=", 1)[1].strip().strip('"')
        vms.append(info)
    return vms


def detect_virsh() -> List[Dict]:
    out = _run_cmd(["virsh", "list", "--all"]) or ""
    vms: List[Dict] = []
    for line in out.splitlines()[2:]:
        if not line.strip():
            continue
        parts = line.split()
        # virsh output: Id Name State
        if len(parts) < 2:
            continue
        name = parts[1]
        info = {"name": name, "hypervisor": "libvirt/virsh", "status": "unknown"}
        dominfo = _run_cmd(["virsh", "dominfo", name]) or ""
        for l in dominfo.splitlines():
            if l.strip().startswith("State:"):
                info["status"] = l.split(":", 1)[1].strip()
            if l.strip().startswith("CPU(s):"):
                info["vcpus"] = l.split(":", 1)[1].strip()
            if l.strip().startswith("Max memory:"):
                info["memory_kb"] = l.split(":", 1)[1].strip()
        # try to get IP (best-effort)
        ipout = _run_cmd(["virsh", "domifaddr", name, "--source", "agent"]) or ""
        for l in ipout.splitlines():
            if "ipv4" in l or "ipv6" in l:
                pieces = l.split()
                if len(pieces) >= 4:
                    info.setdefault("addresses", []).append(pieces[3])
        vms.append(info)
    return vms


def detect_hyperv() -> List[Dict]:
    if platform.system().lower() != "windows":
        return []
    cmd = [
        "powershell",
        "-NoProfile",
        "-Command",
        "Get-VM | Select-Object Name,State,MemoryAssigned,ProcessorCount | ConvertTo-Json",
    ]
    out = _run_cmd(cmd) or ""
    if not out.strip():
        return []
    try:
        parsed = json.loads(out)
    except Exception:
        return []
    vms: List[Dict] = []
    if isinstance(parsed, dict):
        parsed = [parsed]
    for entry in parsed:
        info = {
            "name": entry.get("Name"),
            "hypervisor": "Hyper-V",
            "status": entry.get("State"),
            "memory_mb": entry.get("MemoryAssigned"),
            "vcpus": entry.get("ProcessorCount"),
        }
        vms.append(info)
    return vms


def detect_vmrun() -> List[Dict]:
    """Detect VMs managed by VMware Workstation/Player via `vmrun`.

    Requires `vmrun` (part of VMware VIX or Workstation) on PATH. Returns
    entries with `name`, `hypervisor='vmrun'` and optional `path` and `status`.
    """
    out = _run_cmd(["vmrun", "list"]) or ""
    vms: List[Dict] = []
    # vmrun output typically contains a header line like: "Total running VMs: X"
    for line in out.splitlines():
        line = line.strip()
        if not line or line.lower().startswith("total running"):
            continue
        # treat line as path to .vmx
        info = {"name": line.split('/')[-1].rsplit('.', 1)[0], "hypervisor": "vmrun", "path": line, "status": "running"}
        # try to get guest ip (best-effort)
        ip = _run_cmd(["vmrun", "getGuestIPAddress", line])
        if ip:
            info.setdefault("addresses", []).append(ip.strip())
        vms.append(info)
    return vms


def detect_govc() -> List[Dict]:
    """Detect VMs via `govc` (vSphere CLI). This is best-effort and requires
    `govc` configured (GOVC_URL, GOVC_USERNAME, GOVC_PASSWORD or environment).
    """
    out = _run_cmd(["govc", "vm.info", "-json"]) or ""
    vms: List[Dict] = []
    if not out:
        return vms
    try:
        parsed = json.loads(out)
    except Exception:
        return vms
    # govc vm.info -json returns an object containing VirtualMachines list
    vm_list = []
    if isinstance(parsed, dict):
        # common shapes: {"VirtualMachines": [ ... ]} or {"VirtualMachines": {...}}
        vm_list = parsed.get("VirtualMachines") or []
    if isinstance(vm_list, dict):
        vm_list = [vm_list]
    for entry in vm_list:
        try:
            name = entry.get("Config", {}).get("Name") or entry.get("Name") or entry.get("Path")
        except Exception:
            name = None
        info = {"name": name or "unknown", "hypervisor": "govc", "status": entry.get("Runtime", {}).get("PowerState") if isinstance(entry, dict) else "unknown"}
        # try to extract guest ip
        try:
            guest = entry.get("Guest") or {}
            ip = None
            if isinstance(guest, dict):
                ip = guest.get("IpAddress") or guest.get("Net", [{}])[0].get("IpAddress") if guest.get("Net") else None
            if ip:
                if isinstance(ip, list):
                    info.setdefault("addresses", []).extend(ip)
                else:
                    info.setdefault("addresses", []).append(ip)
        except Exception:
            pass
        vms.append(info)
    return vms


def detect_local_vms() -> List[Dict]:
    """Run all detectors and return combined list.

    This function is intentionally non-blocking for missing tools: it just
    collects whatever detectors succeed.
    """
    results: List[Dict] = []
    # VirtualBox
    try:
        vb = detect_virtualbox()
        results.extend(vb)
    except Exception:
        pass
    # libvirt
    try:
        vir = detect_virsh()
        results.extend(vir)
    except Exception:
        pass
    # Hyper-V
    try:
        hv = detect_hyperv()
        results.extend(hv)
    except Exception:
        pass

    return results


if __name__ == "__main__":
    import pprint

    pprint.pprint(detect_local_vms())
