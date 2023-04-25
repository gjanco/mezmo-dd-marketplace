from .cds_netapp_ontap_utils import ingest_metric


class ClusterIngestor:
    def __init__(self, instance_check) -> None:
        self.instance_check = instance_check
        self.client = instance_check.client
        self.log = self.instance_check.log

    def number_of_nodes(self, cluster_list):
        # set of cluster uuid for distinct count of clusters
        node_uuid = set()
        for cluster in cluster_list:
            node_uuid.add(cluster.get("node-uuid"))
        ingest_metric(
            self.instance_check,
            "dc_cluster_node_uuid",
            len(node_uuid),
        )

    def ingestor(self):
        try:
            results = {}
            if self.client.isClustered():
                results = self.client.queryApi("cluster-node-get-iter")

            if not results.get("attributes-list"):
                self.log.info("NETAPP ONTAP INFO: Nothing to ingest in Cluster details.")
                return

            cluster_list = results["attributes-list"].get("cluster-node-info") or []
            if isinstance(cluster_list, dict):
                cluster_list = [cluster_list]

            self.number_of_nodes(cluster_list)
        except Exception as err:
            self.log.error("NETAPP ONTAP ERROR: Error occurred while ingesting 'Cluster' Data.")
            self.log.exception(err)
