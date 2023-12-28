import snAPI
import xml.etree.ElementTree as ET

# 

class PubMedClient(snAPI.API):
    def __init__(self, key):
        super().__init__(key=snAPI.Key(api_key=key))
        self.add_endpoint("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi", name="search", method="POST")
        self.add_endpoint("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi", name="summary")
        self.add_endpoint("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi", name="fetch")

    def get_ids_from_search(self, text, num=100):
        res = self.search(db='pubmed', term=text, retmax=num)
        root = ET.fromstring(res.output)
        ids = []
        for child in root:
            if child.tag == 'IdList':
                for id_ in child:
                    ids.append(id_.text)
        return ids


pubmed = PubMedClient('[YOUR API KEY]')

ids = pubmed.get_ids_from_search('Therapy[MeSH Subheading] and "glioma"')

print(ids)

summary = pubmed.summary(id=ids[0])

print(summary.output) # an xml file