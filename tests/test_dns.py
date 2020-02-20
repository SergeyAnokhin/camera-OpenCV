import logging, unittest, sys, datetime, os, json
from django.conf import settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "web.settings.test")
from Common.CommonHelper import CommonHelper
from Pipeline.Pipeline import Pipeline
from Providers.DnsAdGuardProvider import DnsAdGuardProvider
from Processors.ElasticSearchDnsProcessor import ElasticSearchDnsProcessor
from tests.TestHelper import TestHelper

# from Common.AppSettings import AppSettings

class TestDns(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestDns, self).__init__(*args, **kwargs)
        self.testHelper = TestHelper()
        self.log = self.testHelper.CreateLog(TestDns.__name__)

    def setUp(self):
        self.testHelper.setUp(self.log, self._testMethodName)

    def tearDown(self):
        self.testHelper.tearDown(self.log, self._testMethodName)

    def test_provider(self):
        # python -m unittest tests.test_dns.TestDns.test_provider
        pipeline = Pipeline(self.log)
        pipeline.providers.append(DnsAdGuardProvider())

        context = {}
        pipeline.Get(context)
        data = context['data']

        self.assertEqual(len(data), 6)
        self.assertEqual(data[5]['client'], '192.168.1.12')
        self.assertEqual(data[5]['client_id'], 12)
        self.assertEqual(data[5]['elapsedMs'], 12.18)
        self.assertEqual(data[5]['@timestamp'], '2020-02-14T23:17:05.783Z')
        self.assertEqual(data[5]['_index'], 'dns-2020.02')
        self.assertEqual(data[5]['_id'], '192.168.1.12@2020-02-14T23:17:05.783Z_m23.cloudmqtt.com')

    def test_processor(self):
        # python -m unittest tests.test_dns.TestDns.test_processor
        provider_output = json.loads("""
{
    "answer": [
        {
            "ttl": 300,
            "type": "CNAME",
            "value": "ec2-54-76-137-235.eu-west-1.compute.amazonaws.com."
        }
    ],
    "client": "192.168.1.12",
    "elapsedMs": 12.18,
    "question": {
        "class": "IN",
        "host": "m23.cloudmqtt.com",
        "type": "AAAA"
    },
    "reason": "NotFilteredNotFound",
    "status": "NOERROR",
    "client_id": 12,
    "client_ip": "192.168.1.12",
    "@timestamp": "2020-02-14T23:17:05.783Z",
    "tags": [
        "camera_tools"
    ],
    "_index": "dns-2020.02",
    "_id": "192.168.1.12@2020-02-14T23:17:05.783Z_m23.cloudmqtt.com"
}        
        """)
        pipeline = Pipeline(self.log)
        pipeline.processors.append(ElasticSearchDnsProcessor(isSimulation=True))

        context = {
            "data": [provider_output]
        }
        pipeline.Process(context)

        meta = context['meta']['ESDNS']["192.168.1.12@2020-02-14T23:17:05.783Z_m23.cloudmqtt.com"]
        generated = meta['_source']

        expected = json.loads("""
{
    "answer": [
        {
            "ttl": 300,
            "type": "CNAME",
            "value": "ec2-54-76-137-235.eu-west-1.compute.amazonaws.com."
        }
    ],
    "client": "192.168.1.12",
    "elapsedMs": 12.18,
    "question": {
        "class": "IN",
        "host": "m23.cloudmqtt.com",
        "type": "AAAA"
    },
    "reason": "NotFilteredNotFound",
    "status": "NOERROR",
    "client_id": 12,
    "client_ip": "192.168.1.12",
    "@timestamp": "2020-02-14T23:17:05.783Z",
    "tags": [
        "camera_tools"
    ]
}
        """)

        self.assertEqual(generated['@timestamp'], expected['@timestamp'])
        self.assertDictEqual(generated, expected)

    # def test_real(self):
    #     pipeline = Pipeline(self.log)
    #     pipeline.providers.append(DnsAdGuardProvider())
    #     pipeline.processors.append(ElasticSearchDnsProcessor()) # isSimulation=True

    #     context = {}
    #     pipeline.Get(context)
    #     pipeline.Process(context)