# connectivity
import requests
import urllib3
from httplib2 import Http
from urllib.parse import urlencode

# data serialization and parsing
import re
import argparse
import json
from lxml import etree

import utils
import const


def load_text_stream(url, ua=const.USER_AGENT):
    # print("load_page():", url)
    h = Http()
    headers = {'User-Agent': ua}

    resp, content = h.request(url, 'GET', headers=headers)
    c = ""
    try:
        c = str(content, encoding='utf8', errors='ignore')
    except UnicodeEncodeError:
        pass

    return resp, c


def do_query(search_query=None, id_list=None, start=0, max_results=10):
    baseurl = "http://export.arxiv.org/api/query?"

    param_list = ""
    if type(search_query) is str and search_query != "":
        search_query = search_query.replace("&", " ").replace("=", " ")
        search_query = search_query.replace("  ", " ").replace(" ", "+") + "&"
        param_list += "search_query=" + search_query

    if type(id_list) is list:
        s_id_list = ""
        for s_id in id_list:
            s_id_list += s_id.__str__() + ","

        s_id_list = s_id_list[0: -1]

        param_list += "id_list=" + s_id_list + "&"

    elif type(id_list) is str and id_list != "":
        param_list += "id_list=" + id_list + "&"

    param_list += "start=" + str(start) + "&"
    param_list += "max_results=" + str(max_results)

    url = baseurl + param_list

    resp, cont = load_text_stream(url)

    if resp['status'] == '200':
        lxml_etree = etree.fromstring(cont.encode('utf8'))

        feed = {}

        # print(entries)
        # element:{.tag: str, .tail: element, .text: str, .attrib: <class 'lxml.etree._Attrib'>}

        title = lxml_etree.xpath("/atom:feed/atom:title", namespaces=const.xml_namespace)[0]
        feed["xml"] = cont
        feed["title"] = {"attrib": dict(title.attrib), "text": title.text}

        results_total = lxml_etree.xpath("/atom:feed/opensearch:totalResults", namespaces=const.xml_namespace)[0]
        results_start = lxml_etree.xpath("/atom:feed/opensearch:startIndex", namespaces=const.xml_namespace)[0]
        results_count = lxml_etree.xpath("/atom:feed/opensearch:itemsPerPage", namespaces=const.xml_namespace)[0]
        feed["opensearch"] = {}
        feed["opensearch"]["result-statics"] = {"total": int(results_total.text),
                                                "start-index": int(results_start.text),
                                                "count": int(results_count.text)}

        feed["entries"] = []
        entries = lxml_etree.xpath("/atom:feed/atom:entry", namespaces=const.xml_namespace)

        for e in entries:
            ent_url = e.xpath("./atom:id", namespaces=const.xml_namespace)
            if len(ent_url) > 0:
                ent_url = e.xpath("./atom:id", namespaces=const.xml_namespace)[0].text
            else:
                continue
            ent_url = e.xpath("./atom:id", namespaces=const.xml_namespace)[0].text
            ent_updated = e.xpath("./atom:updated", namespaces=const.xml_namespace)[0].text
            ent_published = e.xpath("./atom:published", namespaces=const.xml_namespace)[0].text
            ent_title = e.xpath("./atom:title", namespaces=const.xml_namespace)[0].text

            ent_summary = e.xpath("./atom:summary", namespaces=const.xml_namespace)
            if len(ent_summary) > 0:
                ent_summary = ent_summary[0].text
            else:
                ent_summary = ""

            ent_comment = e.xpath("./arxiv:comment", namespaces=const.xml_namespace)
            if len(ent_comment) > 0:
                ent_comment = ent_comment[0].text
            else:
                ent_comment = ""

            ent_authors = []
            for a in e.xpath("./atom:author/atom:name", namespaces=const.xml_namespace):
                ent_authors.append(a.text)

            ent_related_links = []
            for l in e.xpath("./atom:link", namespaces=const.xml_namespace):
                ent_related_links.append(dict(l.attrib))

            ent_category = []
            for c in e.xpath("./arxiv:primary_category/arxiv:category", namespaces=const.xml_namespace):
                ent_category.append(dict(c.attrib))

            ent_prim_cate = dict(e.xpath("./arxiv:primary_category", namespaces=const.xml_namespace)[0].attrib)
            ent_prim_cate["category"] = ent_category

            ent = {"url": ent_url,
                   "time": {"updated": ent_updated, "published": ent_published},
                   "title": ent_title,
                   "summary": ent_summary,
                   "comment": ent_comment,
                   "authors": ent_authors,
                   "related-links": ent_related_links,
                   "category": ent_prim_cate}

            feed["entries"].append(ent)

        resp["feed"] = feed
    else:
        resp["feed"] = None

    return resp


def get_query_string(op_tree):
    """
        :param op_tree: operation tree that form a search
        optree = {"op": "and",
                  "term1": {"op":"ti", "term1": "search in title"},
                  "term2": {
                      "op":"abs", "term": "search text in abstract"
                  }
                 }

        operations:
            ti: Title
            au: Author
            abs: Abstract
            co: Comment
            jr: Journal Reference
            cat: Subject Category
            rn: Report Number
            id: ID(use id list to get rid of document versions)
            all: all of the above

            and:
            or:
            andnot:

    :return:
    """

    if type(op_tree) is str:
        return "all:" + op_tree

    if "op" not in op_tree:

        if "term" in op_tree:
            return "all:" + op_tree["term"].__str__()
        elif "term1" in op_tree:
            return "all:" + op_tree["term1"].__str__()
        else:
            return

    else:
        op = op_tree["op"].__str__()

        if op in "ti,au,abs,co,jr,cat,rn,id,all".split(","):
            if "term" in op_tree:
                return op + ":" + op_tree["term"].__str__()

        if "term1" in op_tree and "term2" in op_tree:
            t1 = get_query_string(op_tree["term1"])
            t2 = get_query_string(op_tree["term2"])

            if t1 is None or t2 is None:
                return None

            if op == "and":
                return "(" + t1 + " AND " + t2 + ")"
            elif op == "or":
                return "(" + t1 + " OR " + t2 + ")"
            elif op == "andnot":
                return "(" + t1 + " ANDNOT " + t2 + ")"

        elif "term" in op_tree:
            return "all:" + op_tree["term"]

        return None


def do_search(query, ua=const.USER_AGENT, **kwargs):
    """

    :param query:
    :param ua: user agent
    :param kwargs:
        working key-value pairs in kwargs:
            max_results: int
            start: int
            sortBy: "relevance", "lastUpdatedDate", "submittedDate"
            sortOrder: "ascending", "descending"
    :return:
    """

    query = query.replace(":", " ")

    url = 'http://export.arxiv.org/api/query?search_query=all:${Q}'.replace("${Q}", query)
    para_start, para_max_results = "start=0", "max_results=10"

    if "max_results" not in kwargs:
        url = url + "&" + para_max_results

    if "start" not in kwargs:
        url = url + "&" + para_start

    for key in kwargs:
        url += "&" + key + "=" + kwargs[key].__str__()

    url = url.replace("  ", " ").replace(" ", "+")

    url = urlencode(url)

    resp, cont = load_text_stream(url, ua)
    return resp, cont


def check_id(id_name):

    if const.REG_IS_ARXIV_ID.match(id_name):
        return True

    return False


# if __name__ == '__main__':
#
#     v = get_query_string({"op": "and", "term1": {"op": "abs", "term": "asdfasdf"}, "term2": "asdfa"})
#     print(v)
