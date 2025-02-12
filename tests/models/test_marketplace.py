from tenint.models.marketplace import MarketplaceConnector


def test_load_from_pyproject(tmpdir):
    pf = tmpdir.join("pyproject-pass.toml")
    pf.write("""
    [project]
    name = "example-connector"
    version = "0.0.1"
    description = "Example Description"
    dependencies = []

    [project.optional-dependencies]
    testing = []

    [project.urls]
    support = "https://example.com/support"

    [[project.authors]]
    name = "Company"
    email = "support@company.com"

    [tool.tenint.connector]
    title = "Example Connector"
    tags = ["tvm", "example"]
    """)
    mp = MarketplaceConnector.load_from_pyproject(
        pf,
        icon_url="https://somewhere.com/img.png",
        image_url="tenable/connector-example",
    )
    assert mp.name == "Example Connector"
    assert mp.slug == "example-connector"
    assert mp.description == "Example Description"
    assert str(mp.icon_url) == "https://somewhere.com/img.png"
    assert mp.image_url == "tenable/connector-example"
    assert mp.timeout.min == 3600
    assert mp.timeout.max == 86400
    assert mp.timeout.default == 3600
    assert mp.marketplace_tag == "0.0.1"
    assert mp.connector_owner == "Company"
    assert mp.support_contact == "support@company.com"
    assert mp.tags == ["tvm", "example"]
    assert mp.resources.disk == 1024
    assert mp.resources.memory == 1024
    assert mp.resources.cpu_cores == 1
    assert mp.schedule_types == ["daily"]
