#!/usr/bin/env python3

import json
import sys
from pprint import pprint
from urllib.request import urlopen

# region User Input
with urlopen("https://ip-ranges.amazonaws.com/ip-ranges.json") as url:
    data = json.loads(url.read().decode())

all_regions = list(set([p['region'] for p in data['prefixes']]))
all_regions.sort()

if len(sys.argv) < 2:
    print('ERROR: pass one of the following regions as an argument.\n{}'.format(all_regions))
    exit(1)

region = sys.argv[1]

region_cidrs = set()
for p in data['prefixes']:
    if p['region'] == region and p['service'] == 'EC2':
        region_cidrs.add(p['ip_prefix'])
region_cidrs = list(region_cidrs)
region_cidrs.sort()

pprint(list(region_cidrs))
