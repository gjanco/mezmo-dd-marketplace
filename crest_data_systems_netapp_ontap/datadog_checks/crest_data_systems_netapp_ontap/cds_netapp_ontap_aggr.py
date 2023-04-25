from .cds_netapp_ontap_utils import field_alias_generator, field_parser, ingest_logs, ingest_metric


class AggrIngestor:
    def __init__(self, instance_check) -> None:
        self.instance_check = instance_check
        self.client = instance_check.client
        self.log = self.instance_check.log

    def aggregates_contained(self, aggr_list):
        # set of aggregate uuid to calculate unique count aggregates
        aggregate_uuid = set()
        for aggr in aggr_list:
            aggregate_uuid.add(aggr.get("aggregate-uuid" if self.client.isClustered() else "uuid"))

        ingest_metric(
            self.instance_check,
            "dc_aggregate_uuid",
            len(aggregate_uuid),
        )

    def aggregates_summary_field_parser(self, event):
        if self.client.isClustered():
            fields = [
                "aggregate-name",
                "aggregate-uuid",
                "aggr-space-attributes.percent-used-capacity",
                "aggr-volume-count-attributes.flexvol-count",
                "aggr-space-attributes.size-total",
                "aggr-space-attributes.size-available",
                "aggr-space-attributes.size-used",
            ]
        else:
            fields = [
                "name",
                "uuid",
                "aggregate-space-details.aggregate-space-info.aggregate-space.fs-space-info.fs-percent-used-capacity",
                "volume-count",
                "aggregate-space-details.aggregate-space-info.aggregate-space.fs-space-info.fs-size-total",
                "aggregate-space-details.aggregate-space-info.aggregate-space.fs-space-info.fs-size-available",
                "aggregate-space-details.aggregate-space-info.aggregate-space.fs-space-info.fs-size-used",
            ]
        event = field_parser(event, fields)

        alias = {
            "name": ["aggregate-name"],
            "uuid": ["aggregate-uuid"],
            "percent-used-capacity": ["fs-percent-used-capacity"],
            "volume-count": ["flexvol-count"],
            "size-total": ["fs-size-total"],
            "size-available": ["fs-size-available"],
            "size-used": ["fs-size-used"],
        }

        return field_alias_generator(event, alias)

    def aggregates_summary_tag(self, event):
        fields = [
            "name",
            "uuid",
            "volume-count",
        ]
        tags = []
        event = field_parser(event, fields)
        for field in event:
            tags.append(f"{field}:{event.get(field)}")
        return tags

    def aggregates_summary(self, aggr_list):
        events = []
        for aggr in aggr_list:
            event = self.aggregates_summary_field_parser(aggr)
            events.append(event)

            # ingest event as a metric
            ingest_metric(
                self.instance_check,
                "aggregates_summary.size_total",
                event.get("size-total"),
                self.aggregates_summary_tag(event),
            )
            ingest_metric(
                self.instance_check,
                "aggregates_summary.size_available",
                event.get("size-available"),
                self.aggregates_summary_tag(event),
            )
            ingest_metric(
                self.instance_check,
                "aggregates_summary.size_used",
                event.get("size-used"),
                self.aggregates_summary_tag(event),
            )
            ingest_metric(
                self.instance_check,
                "aggregates_summary.percent_used_capacity",
                event.get("percent-used-capacity"),
                self.aggregates_summary_tag(event),
            )

        ingest_logs(
            self.instance_check,
            "aggregates_summary",
            events,
            fn_to_evaluate_event=lambda event: (
                event,
                [
                    f'uuid:{event.get("uuid")}',
                ],
            ),
        )

    def aggregates_raid_details_field_parser(self, event):
        if self.client.isClustered():
            fields = [
                "aggregate-name",
                "aggregate-uuid",
                "aggr-raid-attributes.raid-size",
                "aggr-raid-attributes.raid-status",
                "aggr-raid-attributes.raid-lost-write-state",
            ]
        else:
            fields = ["name", "uuid", "raid-size", "raid-status", "raid-lost-write-state"]
        event = field_parser(event, fields)

        alias = {
            "name": ["aggregate-name"],
            "uuid": ["aggregate-uuid"],
            "raid-size": [],
            "raid-status": [],
            "raid-lost-write-state": [],
        }

        return field_alias_generator(event, alias)

    def aggregates_raid_details_tag(self, event):
        fields = ["name", "uuid", "raid-status", "raid-lost-write-state"]
        tags = []
        event = field_parser(event, fields)
        for field in event:
            tags.append(f"{field}:{event.get(field)}")
        return tags

    def aggregates_raid_details(self, aggr_list):
        for aggr in aggr_list:
            event = self.aggregates_raid_details_field_parser(aggr)

            # ingest raid metrics
            ingest_metric(
                self.instance_check,
                "aggregates_raid_details.raid_size",
                event.get("raid-size"),
                self.aggregates_raid_details_tag(event),
            )

    def aggregates_plex_details_field_parser(self, event):
        fields = [
            "plex-status",
            "is-resyncing",
            "is-online",
            "pool",
        ]
        if self.client.isClustered():
            fields += ["plex-name"]
        else:
            fields += ["name"]
        event = field_parser(event, fields)

        alias = {
            "plex-name": ["name"],
            "plex-status": [],
            "is-resyncing": [],
            "is-online": [],
            "pool": [],
        }

        return field_alias_generator(event, alias)

    def aggregates_plex_details_tag(self, event):
        fields = [
            "plex-name",
            "plex-status",
            "is-resyncing",
            "is-online",
        ]
        tags = []
        event = field_parser(event, fields)
        for field in event:
            tags.append(f"{field}:{event.get(field)}")
        return tags

    def aggregates_plex_details(self, aggr_list):
        for aggr in aggr_list:
            if self.client.isClustered():
                event = aggr.get("aggr-raid-attributes", {}).get("plexes", {}).get("plex-attributes", [])
            else:
                event = aggr.get("plexes", {}).get("plex-info", [])

            if isinstance(event, dict):
                event = self.aggregates_plex_details_field_parser(event)
                # ingest plex metrics
                ingest_metric(
                    self.instance_check,
                    "aggregates_plex_details.pool",
                    event.get("pool"),
                    self.aggregates_plex_details_tag(event),
                )
            elif isinstance(event, list):
                for data in event:
                    _event = self.aggregates_plex_details_field_parser(data)
                    # ingest plex metrics
                    ingest_metric(
                        self.instance_check,
                        "aggregates_plex_details.pool",
                        _event.get("pool"),
                        self.aggregates_plex_details_tag(_event),
                    )

    def ingestor(self):
        try:
            if self.client.isClustered():
                results = self.client.queryApi("aggr-get-iter")
                results = results.get("attributes-list")
            else:
                results = self.client.queryApi("aggr-list-info")
                results = results.get("aggregates")

            if not results:
                self.log.info("NETAPP ONTAP INFO: Nothing to ingest in Aggregate details.")
                return

            aggr_list = results.get("aggr-attributes" if self.client.isClustered() else "aggr-info") or []
            if isinstance(aggr_list, dict):
                aggr_list = [aggr_list]

            self.aggregates_contained(aggr_list)
            self.aggregates_summary(aggr_list)

            self.aggregates_raid_details(aggr_list)
            self.aggregates_plex_details(aggr_list)

        except Exception as err:
            self.log.error("NETAPP ONTAP ERROR: Error occurred while ingesting 'Aggregate' Data.")
            self.log.exception(err)
