from typer.testing import CliRunner

from tenint.cli import app

runner = CliRunner()


def test_init_command(tmp_path):
    result = runner.invoke(app, ['init', '--path', str(tmp_path)])
    if result.exception:
        raise result.exception
    assert result.exit_code == 0
    assert 'Now that you have' in result.stdout
    assert 'skipped' not in result.stdout


def test_init_skip_single_file(tmp_path):
    pyfile = tmp_path.joinpath('pyproject.toml')
    with pyfile.open('w') as fobj:
        fobj.write('something')
    result = runner.invoke(app, ['init', '--path', str(tmp_path)])
    assert result.exit_code == 0
    assert 'Now that you have' in result.stdout
    assert 'pyproject.toml as it' in result.stdout


def test_init_skip_tests(tmp_path):
    tmp_path.joinpath('tests').mkdir()
    result = runner.invoke(app, ['init', '--path', str(tmp_path)])
    assert result.exit_code == 0
    assert 'Now that you have' in result.stdout
    assert 'skipped adding tests' in result.stdout
