from .cds_netapp_ontap_utils import field_alias_generator, field_parser, ingest_logs


class DiskIngestor:
    def __init__(self, instance_check) -> None:
        self.instance_check = instance_check
        self.client = instance_check.client
        self.log = self.instance_check.log

    def disk_details_field_parser(self, event):
        if self.client.isClustered():
            fields = [
                "disk-name",
                "disk-uid",
                "disk-inventory-info.model",
                "disk-inventory-info.disk-type",
                "disk-ownership-info.owner-node-name",
            ]
        else:
            fields = ["name", "disk-uid", "disk-model", "disk-type", "node"]
        event = field_parser(event, fields)

        alias = {
            "name": ["disk-name"],
            "uid": ["disk-uid"],
            "model": ["disk-model"],
            "disk-type": [],
            "node": ["owner-node-name"],
        }

        return field_alias_generator(event, alias)

    def disk_details(self, disk_list):
        events = []
        for disk in disk_list:
            event = self.disk_details_field_parser(disk)
            events.append(event)

        ingest_logs(
            self.instance_check,
            "disk_details",
            events,
            fn_to_evaluate_event=lambda event: (
                event,
                [f'disk-uid:{event.get("disk-uid")}'],
            ),
        )

    def ingestor(self):
        try:
            if self.client.isClustered():
                results = self.client.queryApi("storage-disk-get-iter")
                results = results.get("attributes-list")
            else:
                results = self.client.queryApi("disk-list-info")
                results = results.get("disk-details")

            if not results:
                self.log.info("NETAPP ONTAP INFO: Nothing to ingest in Disk details.")
                return

            disk_list = results.get("storage-disk-info" if self.client.isClustered() else "disk-detail-info") or []
            if isinstance(disk_list, dict):
                disk_list = [disk_list]

            self.disk_details(disk_list)

        except Exception as err:
            self.log.error("NETAPP ONTAP ERROR: Error occurred while ingesting 'Disk' Data.")
            self.log.exception(err)
