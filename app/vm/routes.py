"""Virtual machine routes and views."""

from flask import Blueprint, render_template
from flask_login import login_required
from app.models.vm import VirtualMachine

vm_bp = Blueprint('vm', __name__, url_prefix='/vm')


@vm_bp.route('/')
@login_required
def index():
    """Display the virtual machine overview page."""
    vms = VirtualMachine.query.order_by(VirtualMachine.created_at.desc()).all()
    return render_template(
        'virtual_machines/index.html',
        title='Virtual Machines',
        vms=vms
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
