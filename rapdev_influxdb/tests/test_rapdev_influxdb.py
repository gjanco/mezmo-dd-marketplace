from datadog_checks.rapdev_influxdb import InfluxdbCheck


def test_get_default_config(instance):
    check = InfluxdbCheck("rapdev_influxdb", {}, [instance])
    metric_map = check.get_default_config()
    assert isinstance(metric_map, dict)
    assert metric_map['metrics']
    assert isinstance(metric_map['metrics'][0], dict)


def test_tags_in_instance(instance):
    InfluxdbCheck("rapdev_influxdb", {}, [instance])
    assert 'vendor:rapdev' in instance['tags']
    assert 'influxdb_endpoint:http://localhost:8086/metrics' in instance['tags']
