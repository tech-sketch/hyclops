#!/usr/bin/env python

import os
import sys
import time
import logging
import optparse
import configobj
import traceback
from daemon import DaemonContext
from daemon.pidfile import TimeoutPIDLockFile
from hyclops.queue import MessageQueue

# parse command-line options
parser = optparse.OptionParser()
basedir = os.path.dirname(os.path.abspath(__file__))
parser.add_option('-c', dest="config_file", help="config file location", default=os.path.join(basedir, "hyclops.conf"))
parser.add_option('--pid', dest="pid_file", help="pid file location", default="/tmp/hyclops.pid")
(options, args) = parser.parse_args()

# load config file
try:
    config = configobj.ConfigObj(options.config_file, file_error=True)
except IOError, e:
    sys.exit(e)

if os.path.exists(options.pid_file):
    sys.exit("pid file (%s) already exists" % options.pid_file)

# start daemon
with DaemonContext(pidfile=TimeoutPIDLockFile(options.pid_file, 1), stderr=sys.stderr):
    # logging settings
    log_level = config["logging"]["log_level"]
    log_file = config["logging"]["log_file"]
    log_format = '[%(asctime)s] %(name)s (%(threadName)s) %(levelname)s: %(message)s'
    logging.basicConfig(filename=log_file, level=logging.WARNING, format=log_format)
    logger = logging.getLogger('hyclops')
    logger.setLevel(getattr(logging, log_level))

    # add environments
    for key, value in config["environments"].items():
        os.environ[key] = value

    # create queue
    listen_address = config["hyclops"]["listen_address"]
    listen_port = config["hyclops"]["listen_port"]
    queue = MessageQueue(config)
    try:
        queue.bind(listen_address, listen_port)
        logger.info("Message queue is opened")
    except Exception, e:
        err_msg = "Failed to bind ZeroMQ socket: %s" % str(e)
        logger.error(err_msg)
        sys.exit(err_msg)

    # polling loop
    while True:
        try:
            queue.poll()
            time.sleep(3)
        except (KeyboardInterrupt, SystemExit), e:
            queue.close()
            logger.info("Message queue is closed by %s" % e.__class__.__name__)
            break
        except Exception, e:
            logger.error(traceback.format_exc())
