import re

USER_AGENT = "pyXiv(2.0); python 3; Console;"
xml_namespace = {
    "opensearch": "http://a9.com/-/spec/opensearch/1.1/",
    "arxiv": "http://arxiv.org/schemas/atom",
    'atom': "http://www.w3.org/2005/Atom"}

oai_namespace = {

}

REG_IS_ARXIV_ID = re.compile("^([0-9+]{2}[01][0-9]\.[0-9]+(v[0-9]+){0,1})$")
