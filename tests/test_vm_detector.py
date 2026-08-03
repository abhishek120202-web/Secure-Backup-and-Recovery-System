from pathlib import Path

import app.vm.detector as detector


def test_resolve_vboxmanage_executable_falls_back_to_program_files(monkeypatch):
    monkeypatch.setattr(detector.shutil, 'which', lambda name: None)
    monkeypatch.setattr(Path, 'exists', lambda self: str(self) == r'C:\Program Files\Oracle\VirtualBox\VBoxManage.exe')

    resolved = detector._resolve_vboxmanage_executable()

    assert resolved == r'C:\Program Files\Oracle\VirtualBox\VBoxManage.exe'


def test_detect_virtualbox_extracts_vm_path_from_machine_readable_output(monkeypatch):
    def fake_run_cmd(cmd):
        joined = ' '.join(cmd)
        if joined == 'VBoxManage list vms':
            return '"Ubuntu" {12345}\n'
        if joined == 'VBoxManage showvminfo Ubuntu --machinereadable':
            return 'CfgFile="C:\\Users\\test\\VirtualBox VMs\\Ubuntu\\Ubuntu.vbox"\nVMState=running\nmemory=4096\ncpus=4\n'
        return ''

    monkeypatch.setattr(detector, '_run_cmd', fake_run_cmd)

    vms = detector.detect_virtualbox()

    assert len(vms) == 1
    assert vms[0]['path'] == r'C:\Users\test\VirtualBox VMs\Ubuntu\Ubuntu.vbox'
