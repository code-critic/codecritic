#!/bin/python3
# author: Jan Hybs

import json
import copy


def generate_pie_code(obj: dict):
    centers = [['20%'], ['80%']]
    seriess = list()
    for key, val in obj.items():
        data = list()
        for name, value in val.items():
            data.append(dict(
                name=name,
                y=value
            ))
        series = dict(
            name=key,
            data=data,
            center=centers.pop()
        )
        seriess.append(copy.deepcopy(series))
        if not centers:
            break

    chart = dict(
        plotBackgroundColor=None,
        plotBorderWidth=None,
        plotShadow=False,
        type='pie',
        height=200
    )
    title = dict(
        text=None
    )
    plotOptions = dict(
        pie=dict(
            allowPointSelect=True,
            cursor='pointer',
            dataLabels= dict(
                enabled= False
            ),
            showInLegend=False
        )
    )

    conf = json.dumps(dict(
        chart=chart,
        title=title,
        plotOptions=plotOptions,
        series=seriess
    ), indent=4)
    return conf