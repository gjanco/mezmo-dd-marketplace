import json

import six


def secondLevelDictArray(results):
    """
    Converts a NaElement results set to an array of dicts containing
    elements at the second level of the NaElement tree.
    """
    return generalTwoLevelFlatten(results, json_=False)


def naElementToDict(na_element):
    return recursiveMergeElementsToDict(na_element.element)


def recursiveMergeElementsToDict(element):
    """
    Handle the conversion of elements to dictionaries. This
    method will return either a string or a dict depending on
    the element passed.
    -> If the element has no children, then a
            string of the content, even if empty, will be returned.
    -> If the element has children it will return a dictionary.
            This dictionary will contain a content key if content is
            a non empty string. It will also contain keys for each type
            (name) of child, which will be arrays of either strings or
            dictionaries formed by calling this method recursively.

    Examples:
    (Note: name of root element is always omitted in conversion.)
      {'l0': content='v0'} -> 'v0'
      {'l0': children=[{'l1': 'v1'}]} -> {'l1': 'v1'}
      {'l0': children=[{'l1': 'v1'}]} -> {'l1': 'v1'}
      {'l0': content='cont1' children=[{'l1': 'v1'}]} -> {'content': 'cont1', 'l1': 'v1'}
      {'l0': children=[{'l1a': 'v1'}, {'l1b': 'v2'}]} -> {'l1a': 'v1', 'l1b': 'v2'}
      {'l0': children=[{'l1': 'v1'}, {'l1': 'v2'}]} -> {'l1': ['v1', 'v2']}
        (Note: if siblings have the same name, they are grouped into a list.)
      {'l0': children=[{'l1': [{'l2': 'v2'}]}, {'l1': [{'l2': 'v2'}]}]} -> {'l1': [{'l2': 'v2'}, {'l2': 'v2'}]}
      {'l0': children=[{'l1': 'v1'}, {'l1': [{'l2': 'v2'}]}]} -> {'l1': ['v1', {'l2': 'v2'}]}

    RETURNS dictionary OR string
    """
    children = element["children"]
    content = element["content"]
    if len(children) == 0:
        return element["content"]
    else:
        tmp = {}
        if content != "":
            tmp["content"] = content
        for child in children:
            child_elem = child.element
            child_name = child_elem["name"]
            if child_name not in tmp:
                tmp[child_name] = recursiveMergeElementsToDict(child_elem)
            elif type(tmp[child_name]) is list:
                tmp[child_name].append(recursiveMergeElementsToDict(child_elem))
            elif type(tmp[child_name]) is dict or isinstance(tmp[child_name], six.string_types):
                tmp_array = []
                tmp_array.append(tmp[child_name])
                tmp_array.append(recursiveMergeElementsToDict(child_elem))
                tmp[child_name] = tmp_array
        return tmp


def generalTwoLevelFlatten(results, json_=True):
    """
    Simple flattener for xml responses where we want to
    break events after two levels of wrapper E.G.:
    <results status='passed'>
            <aggregates>
                    <aggr-space-info>
                            EVENT
                    </aggr-space-info>
                    <aggr-space-info>
                            EVENT
                    </aggr-space-info>
                    <aggr-space-info>
                            EVENT
                    </aggr-space-info>
            </aggregates>
    </results>

    RETURNS an array of JSON strings
    """
    out_array = []
    for aggregates in results.children_get():
        for aggr_info in aggregates.children_get():
            tmp = {}
            for child in aggr_info.children_get():
                tmp[child.element["name"]] = recursiveMergeElementsToDict(child.element)
            if json_:
                out_array.append(json.dumps(tmp))
            else:
                out_array.append(tmp)
    return out_array
