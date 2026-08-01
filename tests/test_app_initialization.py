import os

from app import create_app


def test_create_app_creates_instance_directory():
    app = create_app('development')
    assert os.path.isdir(app.instance_path)
