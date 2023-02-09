from .cds_netapp_ontap_perf import PerfHandler
from .cds_netapp_ontap_utils import ingest_metric, perf_response_parser


class SystemPerfIngestor:
    def __init__(self, instance_check) -> None:
        self.instance_check = instance_check
        self.client = instance_check.client
        self.log = self.instance_check.log

        self.perf_handler_obj = PerfHandler("system")

    def ingestor(self):
        try:
            response = self.perf_handler_obj.collect(self.client)
            if not response or not response.get("instances"):
                self.log.info("NETAPP ONTAP INFO: Nothing to ingest in SYSTEM performance data.")
                return

            instances = response["instances"].get("instance-data", list())
            if isinstance(instances, dict):
                instances = [instances]

            for instance in instances:
                event = perf_response_parser(instance.get("counters", dict()).get("counter-data", list()))
                uuid = event.get("instance_uuid")
                name = event.get("instance_name")
                # ingest system details
                ingest_metric(
                    self.instance_check,
                    "system.cpu_busy",
                    event.get("cpu_busy"),
                    [f"uuid:{uuid}", f"name:{name}"],
                )
        except Exception as err:
            self.log.error("NETAPP ONTAP ERROR: Error occurred while ingesting 'System' Data.")
            self.log.exception(err)
