from .cds_netapp_ontap_perf import PerfHandler
from .cds_netapp_ontap_utils import ingest_metric, perf_response_parser


class AggrPerfIngestor:
    def __init__(self, instance_check) -> None:
        self.instance_check = instance_check
        self.client = instance_check.client
        self.log = self.instance_check.log

        self.perf_handler_obj = PerfHandler("aggregate")

    def ingestor(self):
        # collect performance data
        try:
            total_transfer = list()
            response = self.perf_handler_obj.collect(self.client)
            if not response or not response.get("instances"):
                self.log.info("NETAPP ONTAP INFO: Nothing to ingest in AGGR performance data.")
                return

            instances = response["instances"].get("instance-data", list())
            if isinstance(instances, dict):
                instances = [instances]

            for instance in instances:
                event = perf_response_parser(instance.get("counters", dict()).get("counter-data", list()))
                # Calculate metrics fields
                total_transfer.append(int(event.get("total_transfers")))

            ingest_metric(
                self.instance_check,
                "aggr.avg_total_transfer",
                ((sum(total_transfer)) / len(total_transfer)),
            )
            ingest_metric(
                self.instance_check,
                "aggr.max_total_transfer",
                (max(total_transfer)),
            )
        except Exception as err:
            self.log.error("NETAPP ONTAP ERROR: Error occurred while ingesting 'Aggregate Performance' Data.")
            self.log.exception(err)
