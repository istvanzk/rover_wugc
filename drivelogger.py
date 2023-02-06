# -*- coding: utf-8 -*-
# 4tronix M.A.R.S. Rover Robot remote control using the PiHut Wireless USB Game Controller
#
#  Copyright 2023 Istvan Z. Kovacs. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

"""Implements the custom logging for the driveRover_wugc"""

import logging
import logging.config

### Logging parameters
ROOT_LOGLEVEL = 'INFO'
FILE_LOGLEVEL = 'INFO'
CONS_LOGLEVEL = 'WARNING' #'CRITICAL'
LOGFILEBYTES = 3*102400
LOG_FILENAME = 'driverover.log'

### Define the logging filter
# Filter out all messages which do include the indicated string
class NoStringFilter(logging.Filter):

    def __init__(self, filter_str=None):
        logging.Filter.__init__(self, filter_str)
        self.filterstr = filter_str

    def filter(self, rec):
        if self.filterstr is None:
            allow = True
        else:
            allow = self.filterstr not in rec.getMessage()

        return allow

### Define the logging configuration
DRIVELOG = {
    'version': 1,
    'disable_existing_loggers': 'False',
    'root': {
        'level': ROOT_LOGLEVEL,
        'handlers': ['file', 'console']
    },
    'formatters': {
        'full': {
            'format': '%(asctime)s [%(levelname)s] (%(threadName)-10s) %(message)s'
        },
        'short': {
            'format': '%(asctime)s %(message)s'
        }
    },
    'handlers': {
        'file': {
            'level': FILE_LOGLEVEL,
            'class': 'logging.handlers.RotatingFileHandler',
            'mode': 'w',
            'maxBytes': LOGFILEBYTES,
            'backupCount': 3,
            'formatter': 'full',
            'filename': LOG_FILENAME, 
            'filters': ['NotMainJob'],
        },
        'console': {
            'level': CONS_LOGLEVEL,
            'class': 'logging.StreamHandler',
            'formatter': 'short',
        }
    },
    'filters':{
        'NotMainJob': {
            '()': NoStringFilter,
            'filter_str': 'noroot',
        }
    },
    'loggers': {
        'info': {
            'handlers': ['file', 'console'],
            'level': 'INFO'
        },
        'debug': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG'
        },
        'warning': {
            'handlers': ['file', 'console'],
            'level': 'WARNING'
        },
        'error': {
            'handlers': ['file', 'console'],
            'level': 'ERROR'
        }
    }
}

### Build the logger instance
def drive_logger():
    """Build and return the logger.
    :return: logger -- Logger instance
    """
    # Use the PRILOGGING logger configuration
    logging.config.dictConfig(DRIVELOG)
    _logger = logging.getLogger()

    return _logger


driveLogger = drive_logger()
