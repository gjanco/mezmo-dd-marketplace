from .cds_netapp_ontap_utils import field_alias_generator, field_parser, ingest_logs, ingest_metric


class VolumeIngestor:
    def __init__(self, instance_check) -> None:
        self.instance_check = instance_check
        self.client = instance_check.client
        self.log = self.instance_check.log

    def volume_details_field_parser(self, event):
        fields = [
            "volume-id-attributes.owning-vserver-name",
            "volume-id-attributes.name",
            "volume-space-attributes.size-total",
            "volume-space-attributes.size-available",
            "volume-state-attributes.state",
            "volume-id-attributes.uuid",
            "volume-space-attributes.size-used",
        ]

        if self.client.isClustered():
            fields += [
                "volume-id-attributes.containing-aggregate-name",
                "volume-space-attributes.percentage-size-used",
                "volume-space-attributes.percentage-snapshot-reserve",
            ]
        else:
            fields += ["containing-aggregate", "percentage-used", "snapshot-percent-reserved"]
        event = field_parser(event, fields)

        alias = {
            "vserver": ["owning-vserver-name"],
            "name": [],
            "percentage-size-used": ["percentage-used"],
            "size-total": [],
            "size-available": [],
            "size-used": [],
            "state": [],
            "uuid": [],
            "aggregate": ["containing-aggregate-name", "containing-aggregate"],
            "percentage-snapshot-reserve": ["snapshot-percent-reserved"],
        }

        return field_alias_generator(event, alias)

    def volume_details_tags_generator(self, event):
        fields = [
            "vserver",
            "name",
            "state",
            "uuid",
            "aggregate",
        ]
        tags = []
        event = field_parser(event, fields)
        for field in event:
            tags.append(f"{field}:{event.get(field)}")
        return tags

    def volume_details(self, volume_list):
        events = []
        # set of cluster uuid for distinct count of clusters
        volume_uuid = set()
        for volume in volume_list:
            event = self.volume_details_field_parser(volume)
            events.append(event)

            volume_uuid.add(event.get("uuid"))

            ingest_metric(
                self.instance_check,
                "volume_details.size_total",
                event.get("size-total"),
                self.volume_details_tags_generator(event),
            )
            ingest_metric(
                self.instance_check,
                "volume_details.percentage-size-used",
                event.get("percentage-size-used"),
                self.volume_details_tags_generator(event),
            )
            ingest_metric(
                self.instance_check,
                "volume_details.percentage-snapshot-reserve",
                event.get("percentage-snapshot-reserve"),
                self.volume_details_tags_generator(event),
            )
            ingest_metric(
                self.instance_check,
                "volume_details.size_used",
                event.get("size-used"),
                self.volume_details_tags_generator(event),
            )
            ingest_metric(
                self.instance_check,
                "volume_details.size_available",
                event.get("size-available"),
                self.volume_details_tags_generator(event),
            )

        ingest_metric(
            self.instance_check,
            "dc_volume_id_attributes_uuid",
            len(volume_uuid),
        )

        ingest_logs(
            self.instance_check,
            "volume_details",
            events,
            fn_to_evaluate_event=lambda event: (
                event,
                [
                    f'uuid:{event.get("uuid")}',
                    f'name:{event.get("name")}',
                ],
            ),
        )

    def vol_associated_aggregate_field_parser(self, event):
        fields = [
            "volume-id-attributes.name",
            "volume-id-attributes.uuid",
        ]

        if self.client.isClustered():
            fields += [
                "volume-id-attributes.containing-aggregate-name",
            ]
        else:
            fields += ["containing-aggregate"]
        event = field_parser(event, fields)

        alias = {
            "name": [],
            "uuid": [],
            "aggregate": ["containing-aggregate-name", "containing-aggregate"],
        }

        return field_alias_generator(event, alias)

    def vol_associated_aggregate_tag(self, event):
        fields = [
            "aggregate",
            "name",
            "uuid",
        ]
        tags = []
        event = field_parser(event, fields)
        for field in event:
            tags.append(f"{field}:{event.get(field)}")
        return tags

    def vol_associated_aggregate(self, volume_list):
        events = []
        # set of cluster uuid for distinct count of clusters
        for volume in volume_list:
            event = self.vol_associated_aggregate_field_parser(volume)
            events.append(event)
        ingest_logs(
            self.instance_check,
            "volume_associate_aggregate",
            events,
            fn_to_evaluate_event=lambda event: (
                event,
                self.vol_associated_aggregate_tag(event),
            ),
        )

    def ingestor(self):
        try:
            if self.client.isClustered():
                results = self.client.queryApi("volume-get-iter")
                results = results.get("attributes-list")
            else:
                results = self.client.queryApi("volume-list-info")
                results = results.get("volumes")

            if not results:
                self.log.info("NETAPP ONTAP INFO: Nothing to ingest in Disk details.")
                return

            volume_list = results.get("volume-attributes" if self.client.isClustered() else "volume-info") or []
            if isinstance(volume_list, dict):
                volume_list = [volume_list]

            self.volume_details(volume_list)
            self.vol_associated_aggregate(volume_list)
        except Exception as err:
            self.log.error("NETAPP ONTAP ERROR: Error occurred while ingesting 'Volume' Data.")
            self.log.exception(err)
