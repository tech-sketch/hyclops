#!/usr/bin/env python

# HyClops for Zabbix
# Copyright 2013 TIS Inc.
# 
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import sys
import datetime
from boto.ec2 import cloudwatch

if len(sys.argv) <= 2:
    print -1,
    sys.exit("Usage: %s {aws_access_key} {aws_secret_key}" % sys.argv[0])
else:
    key = sys.argv[1]
    secret = sys.argv[2]

region = "us-east-1"  # billing status belongs to us-east-1
conn = cloudwatch.connect_to_region(region, aws_access_key_id=key, aws_secret_access_key=secret)
statistics = conn.get_metric_statistics(
    period=300,
    start_time=datetime.datetime.now() - datetime.timedelta(days=1),
    end_time=datetime.datetime.now(),
    metric_name="EstimatedCharges",
    namespace="AWS/Billing",
    statistics=["Maximum"],
    dimensions={"Currency": "USD"},
    unit=None
)

statistics = sorted(statistics, key=lambda stat: stat["Timestamp"], reverse=True)
# return latest data
print statistics[0]["Maximum"],
