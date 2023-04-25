from .cds_netapp_ontap_perf import PerfHandler
from .cds_netapp_ontap_utils import ingest_metric, perf_response_parser


class DiskPerfIngestor:
    def __init__(self, instance_check) -> None:
        self.instance_check = instance_check
        self.client = instance_check.client
        self.log = self.instance_check.log

        self.perf_handler_obj = PerfHandler("disk")

    def ingestor(self):
        # collect performance data
        try:
            response = self.perf_handler_obj.collect(self.client)
            avg_read_latency = []
            if not response or not response.get("instances"):
                self.log.info("NETAPP ONTAP INFO: Nothing to ingest in Disk performance data.")
                return

            instances = response["instances"].get("instance-data", [])
            if isinstance(instances, dict):
                instances = [instances]

            for instance in instances:
                event = perf_response_parser(instance.get("counters", {}).get("counter-data", []))

                uuid = instance.get("uuid", "")
                name = event.get("display_name", "")

                # Calculate necessary metrics value
                avg_read_latency.append(int(event.get("user_read_latency")))
                # Disk Details Dashboards
                # ingest metrics for Selected Disk LATENCY
                ingest_metric(
                    self.instance_check,
                    "disk.user_read_latency",
                    event.get("user_read_latency"),
                    [f"uuid:{uuid}", f"name:{name}"],
                )
                ingest_metric(
                    self.instance_check,
                    "disk.user_write_latency",
                    event.get("user_write_latency"),
                    [f"uuid:{uuid}", f"name:{name}"],
                )
                ingest_metric(
                    self.instance_check,
                    "disk.cp_read_latency",
                    event.get("cp_read_latency"),
                    [f"uuid:{uuid}", f"name:{name}"],
                )
                # ingest metrics for Data Transfer Rates
                ingest_metric(
                    self.instance_check,
                    "disk.user_read_blocks",
                    event.get("user_read_blocks"),
                    [f"uuid:{uuid}", f"name:{name}"],
                )
                ingest_metric(
                    self.instance_check,
                    "disk.user_write_blocks",
                    event.get("user_write_blocks"),
                    [f"uuid:{uuid}", f"name:{name}"],
                )
                ingest_metric(
                    self.instance_check,
                    "disk.cp_read_blocks",
                    event.get("cp_read_blocks"),
                    [f"uuid:{uuid}", f"name:{name}"],
                )
                ingest_metric(
                    self.instance_check,
                    "disk.skip_blocks",
                    event.get("skip_blocks"),
                    [f"uuid:{uuid}", f"name:{name}"],
                )
                # ingest metrics for Disk busy percent
                if event.get("disk_busy", "").isdigit() and event.get("base_for_disk_busy", "").isdigit():
                    disk_busy_percent = int(event["disk_busy"]) * 100 / int(event["base_for_disk_busy"])
                    ingest_metric(
                        self.instance_check,
                        "disk.disk_busy_percent",
                        round(disk_busy_percent),
                        [f"uuid:{uuid}", f"name:{name}"],
                    )

            ingest_metric(
                self.instance_check,
                "disk.max_user_read_latency",
                max(avg_read_latency),
                [f"uuid:{uuid}", f"name:{name}"],
            )
            ingest_metric(
                self.instance_check,
                "disk.avg_user_read_latency",
                ((sum(avg_read_latency)) / (len(avg_read_latency))),
                [f"uuid:{uuid}", f"name:{name}"],
            )

        except Exception as err:
            self.log.error("NETAPP ONTAP ERROR: Error occurred while ingesting 'Disk Performance' Data.")
            self.log.exception(err)
