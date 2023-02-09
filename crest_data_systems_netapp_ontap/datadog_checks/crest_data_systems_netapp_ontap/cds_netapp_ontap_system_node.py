from .cds_netapp_ontap_utils import field_alias_generator, field_parser, ingest_metric


class SystemNodeIngestor:
    def __init__(self, instance_check) -> None:
        self.instance_check = instance_check
        self.client = instance_check.client
        self.log = self.instance_check.log

    def system_node_summary_field_parser(self, event):
        if self.client.isClustered():
            fields = [
                "node",
                "node-location",
                "node-model",
                "node-uptime",
                "node-serial-number",
                "is-node-healthy",
                "nvram-battery-status",
                "env-failed-fan-count",
                "env-failed-power-supply-count",
                "env-over-temperature",
            ]
        event = field_parser(event, fields)

        alias = {
            "node": [],
            "node-location": [],
            "node-model": [],
            "node-uptime": [],
            "node-serial-number": [],
            "is-node-healthy": [],
            "battery-status": ["nvram-battery-status"],
            "failed-fan-count": ["env-failed-fan-count"],
            "failed-power-supply-count": ["env-failed-power-supply-count"],
            "is-over-temperature": ["env-over-temperature"],
        }

        return field_alias_generator(event, alias)

    def system_node_summary_tag(self, event):
        fields = [
            "node",
            "node-location",
            "node-model",
            "node-serial-number",
            "battery-status",
            "is-node-healthy",
            "is-over-temperature",
        ]
        tags = list()
        event = field_parser(event, fields)
        for field in event:
            tags.append(f"{field}:{event.get(field)}")
        return tags

    def system_node_summary(self, system_node_list):
        events = list()
        for system_node in system_node_list:
            event = self.system_node_summary_field_parser(system_node)
            events.append(event)

            # ingest event as a metric
            ingest_metric(
                self.instance_check,
                "system_node_summary.failed_fan_count",
                event.get("failed-fan-count"),
                self.system_node_summary_tag(event),
            )
            ingest_metric(
                self.instance_check,
                "system_node_summary.failed_power_supply_count",
                event.get("failed-power-supply-count"),
                self.system_node_summary_tag(event),
            )

    def ingestor(self):
        try:
            results = None
            if self.client.isClustered():
                results = self.client.queryApi("system-node-get-iter")
                results = results.get("attributes-list")

            if not results:
                self.log.info("NETAPP ONTAP INFO: Nothing to ingest in System Node details.")
                return

            system_node_list = results.get("node-details-info") or list()
            if isinstance(system_node_list, dict):
                system_node_list = [system_node_list]

            self.system_node_summary(system_node_list)

        except Exception as err:
            self.log.error("NETAPP ONTAP ERROR: Error occurred while ingesting 'System Node' Data.")
            self.log.exception(err)
