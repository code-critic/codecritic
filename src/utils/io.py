#!/bin/python3
# author: Jan Hybs

import os
import time
import shutil
import pathlib

from loguru import logger

ONE_DAY = 60*60*24
HALF_DAY = 60*60*12


def delete_old_files(root: pathlib.Path, seconds=HALF_DAY):
    if root.name not in ('tmp', '.tmp'):
        logger.warning('Aborting deletion of old dirs: folder {} not named tmp', root)
        return False

    deleted = 0
    total = 0
    ts = int(time.time())
    for d in root.glob('*'):
        if d.is_dir():
            modif = int(os.path.getmtime(d))
            total += 1

            if (ts - modif) > seconds:
                try:
                    logger.debug('deletig old file {} ({:1.1f} days old)', d, (ts - modif) / ONE_DAY)
                    shutil.rmtree(str(d), ignore_errors=True)
                    deleted += 1
                except Exception as e:
                    logger.exception('Cannot delete dir %s' % d)

    logger.info('deleted {} out of {} old dirs', deleted, total)
    return deleted

