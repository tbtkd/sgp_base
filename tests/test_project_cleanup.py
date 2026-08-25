from scripts.cleanup_project import cleanup_project


def test_cleanup_project_removes_only_known_obsolete_artifacts(tmp_path):
    old_logo = tmp_path / "app" / "static" / "img" / "logo.svg"
    old_sidebar_styles = tmp_path / "app" / "static" / "css" / "components" / "_sidebar.css"
    current_logo = old_logo.with_name("logo.png")
    bytecode = tmp_path / "app" / "models" / "__pycache__" / "usuario.pyc"
    root_bytecode = tmp_path / "__pycache__" / "run.pyc"
    pytest_cache = tmp_path / ".pytest_cache" / "README.md"
    database = tmp_path / "instance" / "pacientes.db"
    virtualenv_file = tmp_path / ".venv" / "Lib" / "keep.pyc"

    for path in (
        old_logo,
        old_sidebar_styles,
        current_logo,
        bytecode,
        root_bytecode,
        pytest_cache,
        database,
        virtualenv_file,
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"test")

    removed = cleanup_project(tmp_path)

    assert old_logo in removed
    assert not old_logo.exists()
    assert old_sidebar_styles in removed
    assert not old_sidebar_styles.exists()
    assert not bytecode.exists()
    assert not root_bytecode.exists()
    assert not pytest_cache.exists()
    assert current_logo.is_file()
    assert database.is_file()
    assert virtualenv_file.is_file()
