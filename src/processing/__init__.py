#!/bin/python3
# author: Jan Hybs

import os

from cfg.languages import Lang
from cfg.problems import Prob
from cfg.env import variables as env
from cfg.requests import Request
from processing.processor import Processor
from utils import yamlex
from utils.dates import get_datetime

yamlex.extend_yaml()
Lang.read_config(env.lang_conf)
Prob.read_config(env.prob_conf)


def create_request(user, prob_id, lang_id, docker=False, src=None, action=Request.Action.TEST, **kwargs):
    prob = Prob.get(prob_id)
    lang = Lang.get(lang_id)

    conf = {
        'user': user,
        'root': os.path.join(env.tmp, user, prob.id, lang.id, get_datetime()),
        'prob': prob,
        'lang': lang,
        'src': src,
        'action': action,
        'docker': docker,
    }
    conf.update(kwargs)

    return Request(conf)