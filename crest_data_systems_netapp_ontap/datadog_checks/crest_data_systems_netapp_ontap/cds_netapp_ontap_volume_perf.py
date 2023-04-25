from .cds_netapp_ontap_perf import PerfHandler
from .cds_netapp_ontap_utils import ingest_metric, perf_response_parser


class VolumePerfIngestor:
    def __init__(self, instance_check) -> None:
        self.instance_check = instance_check
        self.client = instance_check.client
        self.log = self.instance_check.log

        self.perf_handler_obj = PerfHandler("volume")

    def ingestor(self):
        # collect performance data
        try:
            response = self.perf_handler_obj.collect(self.client)
            avg_latency = []

            if not response or not response.get("instances"):
                self.log.info("NETAPP ONTAP INFO: Nothing to ingest in VOLUME performance data.")
                return

            instances = response["instances"].get("instance-data", [])
            if isinstance(instances, dict):
                instances = [instances]

            for instance in instances:
                uuid = instance.get("uuid", "")
                name = instance.get("name", "")

                event = perf_response_parser(instance.get("counters", {}).get("counter-data", []))

                # ingest metrics of Block Operations
                ingest_metric(
                    self.instance_check,
                    "volume.read_blocks",
                    event.get("read_blocks"),
                    [f"uuid:{uuid}", f"name:{name}"],
                )
                # Required field calculation
                avg_latency.append(int(event.get("avg_latency")))

                # ingest metrics of Block Operations
                ingest_metric(
                    self.instance_check,
                    "volume.read_blocks",
                    event.get("read_blocks"),
                    [f"uuid:{uuid}", f"name:{name}"],
                )
                ingest_metric(
                    self.instance_check,
                    "volume.write_blocks",
                    event.get("write_blocks"),
                    [f"uuid:{uuid}", f"name:{name}"],
                )

                # ingest metrics of cluster and volume details
                ingest_metric(
                    self.instance_check,
                    "volume.read_data",
                    event.get("read_data"),
                    [f"uuid:{uuid}", f"name:{name}"],
                )
                ingest_metric(
                    self.instance_check,
                    "volume.write_data",
                    event.get("write_data"),
                    [f"uuid:{uuid}", f"name:{name}"],
                )
                ingest_metric(
                    self.instance_check,
                    "volume.avg_latency",
                    event.get("avg_latency"),
                    [f"uuid:{uuid}", f"name:{name}"],
                )
                ingest_metric(
                    self.instance_check,
                    "volume.read_latency",
                    event.get("read_latency"),
                    [f"uuid:{uuid}", f"name:{name}"],
                )
                ingest_metric(
                    self.instance_check,
                    "volume.other_latency",
                    event.get("other_latency"),
                    [f"uuid:{uuid}", f"name:{name}"],
                )
                ingest_metric(
                    self.instance_check,
                    "volume.write_latency",
                    event.get("write_latency"),
                    [f"uuid:{uuid}", f"name:{name}"],
                )
                ingest_metric(
                    self.instance_check,
                    "volume.read_ops",
                    event.get("read_ops"),
                    [f"uuid:{uuid}", f"name:{name}"],
                )
                ingest_metric(
                    self.instance_check,
                    "volume.write_ops",
                    event.get("write_ops"),
                    [f"uuid:{uuid}", f"name:{name}"],
                )
                ingest_metric(
                    self.instance_check,
                    "volume.other_ops",
                    event.get("other_ops"),
                    [f"uuid:{uuid}", f"name:{name}"],
                )
                ingest_metric(
                    self.instance_check,
                    "volume.total_ops",
                    event.get("total_ops"),
                    [f"uuid:{uuid}", f"name:{name}"],
                )
            ingest_metric(
                self.instance_check,
                "volume.avg_average_latency",
                (sum(avg_latency) / len(avg_latency)),
            )
            ingest_metric(
                self.instance_check,
                "volume.max_average_latency",
                (max(avg_latency)),
            )
        except Exception as err:
            self.log.error("NETAPP ONTAP ERROR: Error occurred while ingesting 'Volume Perf' Data.")
            self.log.exception(err)
