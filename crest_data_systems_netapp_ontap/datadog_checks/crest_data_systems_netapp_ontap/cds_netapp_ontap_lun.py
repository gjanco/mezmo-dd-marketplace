from .cds_netapp_ontap_utils import field_parser, ingest_logs, ingest_metric


class LunIngestor:
    def __init__(self, instance_check) -> None:
        self.instance_check = instance_check
        self.client = instance_check.client
        self.log = self.instance_check.log

    def lun_inv_details_field_parser(self, event):
        fields = [
            "serial-number",
            "path",
            "online",
            "size",
            "size-used",
            "volume",
            "vserver",
            "uuid",
        ]
        return field_parser(event, fields)

    def lun_inv_details_tags_generator(self, event):
        fields = ["serial-number", "path", "online", "volume", "vserver", "uuid"]
        tags = []
        for field in fields:
            tags.append(f"{field}:{event.get(field, '-')}")
        return tags

    def lun_inventory_details(self, lun_list):
        events = []
        for lun in lun_list:
            # ingest event as a metric
            ingest_metric(
                self.instance_check,
                "lun_inv_details.size",
                int(lun.get("size")) - int(lun.get("size-used")),
                self.lun_inv_details_tags_generator(lun) + ["size-type:available"],
            )
            ingest_metric(
                self.instance_check,
                "lun_inv_details.size",
                lun.get("size-used"),
                self.lun_inv_details_tags_generator(lun) + ["size-type:used"],
            )

            event = self.lun_inv_details_field_parser(lun)
            events.append(event)

        ingest_logs(
            self.instance_check,
            "lun_inventory_details",
            events,
            fn_to_evaluate_event=lambda event: (
                event,
                [f'type:{event.get("uuid")}'],
            ),
        )

    def ingestor(self):
        try:
            if self.client.isClustered():
                results = self.client.queryApi("lun-get-iter")
                results = results.get("attributes-list")
            else:
                results = self.client.queryApi("lun-list-info")
                results = results.get("luns")

            if not results:
                self.log.info("NETAPP ONTAP INFO: Nothing to ingest in LUN details.")
                return

            lun_list = results.get("lun-info") or []
            if isinstance(lun_list, dict):
                lun_list = [lun_list]

            self.lun_inventory_details(lun_list)
        except Exception as err:
            self.log.error("NETAPP ONTAP ERROR: Error occurred while ingesting 'Lun' Data.")
            self.log.exception(err)
