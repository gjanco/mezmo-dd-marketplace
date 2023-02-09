from .NetApp.NaElement import NaElement


class PerfHandler:
    def __init__(self, object_name):
        self.object_name = object_name

    def collect(self, oc):
        """This method collects performance data of given object from server.

        RETURNS"""
        try:
            if oc.isClustered():
                perf_element = NaElement("perf-object-instance-list-info-iter")
            else:
                perf_element = NaElement("perf-object-instance-list-info")
            perf_element.child_add_string("objectname", self.object_name)
            results = oc.queryApi(perf_element)

            if results.get("attributes-list"):
                instances = results["attributes-list"]
            elif results.get("instances"):
                instances = results["instances"]
            else:
                return

            # parse list of instances
            instances = instances.get("instance-info") or list()
            if isinstance(instances, dict):
                instances = [instances]

            # create query for performance data of all instances
            perf_element = NaElement("perf-object-get-instances")
            perf_element.child_add_string("objectname", self.object_name)

            instance_element = NaElement("instances")
            for instance in instances:
                instance_element.child_add_string("instance", instance.get("name"))
            perf_element.child_add(instance_element)

            return oc.queryApi(perf_element)
        except Exception as err:
            oc.log.error(
                "NETAPP ONTAP ERROR: Error occurred while querying API while collecting "  # noqa: G00
                "performance data of '{object_name}'".format(object_name=self.object_name),
            )
            self.log.exception(err)
