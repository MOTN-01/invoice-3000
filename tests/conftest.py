import pytest
import db
import app as flask_app_module


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    db_file = tmp_path / 'test.db'
    monkeypatch.setattr(db, 'DB_PATH', db_file)
    db.init_db()
    yield db_file


@pytest.fixture
def client(isolated_db):
    flask_app_module.app.config['TESTING'] = True
    flask_app_module._pending.clear()
    with flask_app_module.app.test_client() as c:
        yield c
    flask_app_module._pending.clear()
