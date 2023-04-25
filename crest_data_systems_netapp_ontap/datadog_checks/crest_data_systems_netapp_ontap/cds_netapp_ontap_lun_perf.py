from .cds_netapp_ontap_perf import PerfHandler
from .cds_netapp_ontap_utils import ingest_metric, perf_response_parser


class LunPerfIngestor:
    def __init__(self, instance_check) -> None:
        self.instance_check = instance_check
        self.client = instance_check.client
        self.log = self.instance_check.log

        self.perf_handler_obj = PerfHandler("lun")

    def ingestor(self):
        # collect performance data
        try:
            response = self.perf_handler_obj.collect(self.client)

            if not response or not response.get("instances"):
                self.log.info("NETAPP ONTAP INFO: Nothing to ingest in LUN performance data.")
                return

            instances = response["instances"].get("instance-data", [])
            if isinstance(instances, dict):
                instances = [instances]

            for instance in instances:
                uuid = instance.get("uuid", "")
                name = instance.get("name", "")
                event = perf_response_parser(instance.get("counters", {}).get("counter-data", []))

                # ingest metrics for LUN Latency
                ingest_metric(
                    self.instance_check,
                    "lun.avg_latency",
                    event.get("avg_latency"),
                    [f"uuid:{uuid}", f"name:{name}"],
                )
                ingest_metric(
                    self.instance_check,
                    "lun.avg_read_latency",
                    event.get("avg_read_latency"),
                    [f"uuid:{uuid}", f"name:{name}"],
                )
                ingest_metric(
                    self.instance_check,
                    "lun.avg_write_latency",
                    event.get("avg_write_latency"),
                    [f"uuid:{uuid}", f"name:{name}"],
                )

                # ingest metrics for LUN IOPS
                ingest_metric(
                    self.instance_check,
                    "lun.total_ops",
                    event.get("total_ops"),
                    [f"uuid:{uuid}", f"name:{name}"],
                )
                ingest_metric(
                    self.instance_check,
                    "lun.read_ops",
                    event.get("read_ops"),
                    [f"uuid:{uuid}", f"name:{name}"],
                )
                ingest_metric(
                    self.instance_check,
                    "lun.write_ops",
                    event.get("write_ops"),
                    [f"uuid:{uuid}", f"name:{name}"],
                )
        except Exception as err:
            self.log.error("NETAPP ONTAP ERROR: Error occurred while ingesting 'Lun Performance' Data.")
            self.log.exception(err)
