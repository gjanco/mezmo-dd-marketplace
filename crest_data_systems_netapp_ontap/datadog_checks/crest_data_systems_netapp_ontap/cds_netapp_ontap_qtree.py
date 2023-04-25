from .cds_netapp_ontap_utils import field_alias_generator, field_parser, ingest_logs
from .NetApp.NaElement import NaElement


class QTreeIngestor:
    def __init__(self, instance_check) -> None:
        self.instance_check = instance_check
        self.client = instance_check.client
        self.log = self.instance_check.log

    def associated_qtrees_field_parser(self, event):
        fields = ["volume", "id", "qtree", "oplocks", "status", "security-style"]
        event = field_parser(event, fields)

        alias = {
            "volume": [],
            "id": [],
            "qtree": [],
            "oplocks": [],
            "qtree-status": ["status"],
            "security-style": [],
        }

        return field_alias_generator(event, alias)

    def associated_qtrees(self, qtree_list):
        events = []
        # set of cluster uuid for distinct count of clusters
        for qtree in qtree_list:
            event = self.associated_qtrees_field_parser(qtree)
            if event.get("id").isdigit() and int(event["id"]) != 0:
                events.append(event)

        ingest_logs(
            self.instance_check,
            "qtree_associate_aggregate",
            events,
            fn_to_evaluate_event=lambda event: (
                event,
                [
                    f'qtree:{event.get("qtree")}',
                    f'id:{event.get("id")}',
                ],
            ),
        )

    def ingestor(self):
        try:
            if self.client.isClustered():
                results = self.client.queryApi("qtree-list-iter")
                results = results.get("attributes-list")

            else:
                results = self.client.queryApi("qtree-list-iter-start")
                tag = results.get("tag")
                records = results.get("records")

                qtree_next_element = NaElement("qtree-list-iter-next")
                qtree_next_element.child_add_string("tag", tag)
                qtree_next_element.child_add_string("maximum", records)
                results = self.client.queryApi(qtree_next_element)
                results = results.get("qtrees")

            if not results:
                self.log.info("NETAPP ONTAP INFO: Nothing to ingest in qtree details.")
                return

            qtree_list = results.get("qtree-info") or []
            if isinstance(qtree_list, dict):
                qtree_list = [qtree_list]

            self.associated_qtrees(qtree_list)
        except Exception as err:
            self.log.error("NETAPP ONTAP ERROR: Error occurred while ingesting 'QTree' Data.")
            self.log.exception(err)
