#!/bin/python3
# author: Jan Hybs

import yaml
from cfg.languages import Lang
from cfg.problems import Prob


def lang_parse(loader, node):
    return Lang.get(loader.construct_scalar(node).strip())


def prob_parse(loader, node):
    return Prob.get(loader.construct_scalar(node).strip())


def str_presenter(dumper, data):
    if len(data.splitlines()) > 1:  # check for multiline string
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)


def extend_yaml():
    yaml.add_constructor('!language', lang_parse)
    yaml.add_constructor('!lang', lang_parse)

    yaml.add_constructor('!problem', prob_parse)
    yaml.add_constructor('!prob', prob_parse)

    yaml.add_representer(str, str_presenter)