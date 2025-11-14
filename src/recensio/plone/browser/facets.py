from copy import deepcopy
from ZTUtils import make_query

browsing_facets = ["ddcPlace", "ddcTime", "ddcSubject"]


def getSelectedQuery(
    selected, params=None, facet_fields=browsing_facets, queryparam="fq"
):
    """construct a query that gets faceting info with the specified fields selected,
    i.e. set as fq (filter query) fields. Selected should be a dict with field
    (=attribute) names mapped to lists of values
    """
    if not params:
        params = {"facet": "true", "facet.field": facet_fields}
    for field, values in selected.items():
        for name in values:
            if name:
                if queryparam == "fq":
                    params.setdefault(queryparam, []).append(
                        '%s:"%s"' % (field, name)
                    )
                else:
                    params.setdefault(queryparam, []).append(name)
    return make_query(params, doseq=True)



def convertFacets(
    fields,
    context=None,
    request={},
    filter=None,
    facet_fields=browsing_facets,
    queryparam="fq",
):
    """convert facet info to a form easy to process in templates"""
    info = []
    params = request.copy()  # request needs to be a dict, i.e. request.form
    facets = facet_fields
    params["facet.field"] = facets = list(facets)
    fq = params.get(queryparam, [])
    if isinstance(fq, str):
        fq = params[queryparam] = [fq]
    selected = set([facet.split(":", 1)[0].strip("+") for facet in fq])
    selected = selected.intersection(set(browsing_facets))
    for field, values in fields.items():
        counts = []
        for name, count in sorted(list(values.items()), key=lambda x: x[1]):
            p = deepcopy(params)
            # p.setdefault(queryparam, []).append('%s:"%s"' % (field, name.encode('utf-8')))
            if filter is None or filter(name, count):
                counts.append(
                    dict(
                        name=name,
                        count=count,
                        query=getSelectedQuery(
                            {field: [name]},
                            params=p,
                            facet_fields=facet_fields,
                            queryparam=queryparam,
                        ),
                    )
                )
        if counts:
            info.append(dict(title=field, counts=counts))
    if facets:  # sort according to given facets (if available)

        def pos(item):
            try:
                return facets.index(item)
            except ValueError:
                return len(facets)  # position the item at the end

        func = lambda x: pos(x)
    else:  # otherwise sort by title
        func = lambda x: x["title"]
    return sorted(info, key=func)
