"""Virtual machine routes and views."""

from flask import Blueprint, render_template
from flask_login import login_required
from app.models import db
from app.models.vm import VirtualMachine
from app.vm.detector import detect_local_vms

vm_bp = Blueprint('vm', __name__, url_prefix='/vm')


@vm_bp.route('/')
@login_required
def index():
    """Display the virtual machine overview page."""
    # database-backed VMs
    db_vms = VirtualMachine.query.order_by(VirtualMachine.created_at.desc()).all()
    # best-effort local detection (VirtualBox, libvirt, Hyper-V)
    detected = detect_local_vms()

    if not db_vms and not detected:
        demo_vm = VirtualMachine(
            name='Demo VM',
            vm_path='demo-vm',
            uuid='demo-vm-001',
            status='active',
            memory_mb=2048,
            cpu_cores=2,
            disk_size_gb=40.0,
            description='Sample VM entry for local testing and demos'
        )
        db.session.add(demo_vm)
        db.session.commit()
        db_vms = [demo_vm]

    return render_template(
        'virtual_machines/index.html',
        title='Virtual Machines',
        vms=db_vms,
        detected_vms=detected,
    )


@vm_bp.route('/<int:vm_id>')
@login_required
def details(vm_id: int):
    """Display details for a specific virtual machine."""
    vm = VirtualMachine.query.get_or_404(vm_id)
    return render_template(
        'virtual_machines/details.html',
        title=f'VM Details: {vm.name}',
        vm=vm
    )
