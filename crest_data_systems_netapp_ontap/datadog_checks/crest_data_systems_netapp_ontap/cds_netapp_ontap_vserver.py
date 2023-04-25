from .cds_netapp_ontap_utils import ingest_metric


class VServerIngestor:
    def __init__(self, instance_check) -> None:
        self.instance_check = instance_check
        self.client = instance_check.client
        self.log = self.instance_check.log

    def number_of_vserver(self, vserver_list):
        # set of vserver uuid for distinct count of vservers
        vserver_uuid = set()
        for vserver in vserver_list:
            vserver_uuid.add(vserver.get("uuid"))
        ingest_metric(
            self.instance_check,
            "dc_vserver_uuid",
            len(vserver_uuid),
        )

    def ingestor(self):
        try:
            results = {}
            if self.client.isClustered():
                results = self.client.queryApi("vserver-get-iter")

            if not results.get("attributes-list"):
                self.log.info("NETAPP ONTAP INFO: Nothing to ingest in vserver details.")
                return

            vserver_list = results["attributes-list"].get("vserver-info") or []
            if isinstance(vserver_list, dict):
                vserver_list = [vserver_list]

            self.number_of_vserver(vserver_list)
        except Exception as err:
            self.log.error("NETAPP ONTAP ERROR: Error occurred while ingesting 'VServer' Data.")
            self.log.exception(err)
