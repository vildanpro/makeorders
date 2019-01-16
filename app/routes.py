import json
from pprint import pprint
from flask import render_template, redirect, request, make_response
from app import app
import requests


@app.route('/')
def index():
    order_data = None
    suppliers = None
    supplier = None
    list_range_of_periods = None
    start_period_range = None
    end_period_range = None
    first_period = None
    last_period = None
    cod_pl = request.args.get('cod_pl') if request.args.get('cod_pl') else 0
    i_owner = request.args.get('i_owner') if request.args.get('i_owner') else 0
    range_of_periods = request.args.get('range_of_periods')
    all_periods = None

    if cod_pl:
        r = requests.get(f'http://192.168.1.26:8080/v1/get_suppliers/{cod_pl}')
        suppliers = json.loads(r.content)

    if i_owner:
        r = requests.get(f'http://192.168.1.26:8080/v1/get_periods/{cod_pl}/{i_owner}')
        list_range_of_periods = json.loads(r.content)
        first_period = str((list_range_of_periods[0].split('-'))[0])
        last_period = str((list_range_of_periods[-1].split('-'))[-1])
        all_periods = first_period + '-' + last_period
        query = ('{' +
                 f'order(cod_pl: {cod_pl}, i_owner: {i_owner}, range_of_periods: "{all_periods}")' +
                 '''{for_period cod_u servicename i_owner supplier typerec_1 typerec_2 typerec_minus60 
                 typerec_6 typerec_7 typerec_9 typerec_minus66 typerec_minus10 typerec_minus7 typerec_minus6 
                 typerec_minus1 total}}''')
        r = requests.post('http://192.168.1.26:8080/graphql', json={'query': query})
        order_data = (r.json())['data']['order']

    if range_of_periods:
        query = ('{' +
                 f'order(cod_pl: {cod_pl}, i_owner: {i_owner}, range_of_periods: "{range_of_periods}")' +
                 '''{for_period cod_u servicename i_owner supplier typerec_1 typerec_2 typerec_minus60
                  typerec_6 typerec_7 typerec_9 typerec_minus66 typerec_minus10 typerec_minus7 
                  typerec_minus6 typerec_minus1 total}}''')
        r = requests.post('http://192.168.1.26:8080/graphql', json={'query': query})
        range_of_periods = range_of_periods.split('-')
        start_period_range = int(range_of_periods[0])
        end_period_range = int(range_of_periods[1]) + 1
        order_data = (r.json())['data']['order']

    return render_template('index.html',
                           cod_pl=cod_pl if not cod_pl else int(cod_pl),
                           i_owner=i_owner if not i_owner else int(i_owner),
                           all_periods=all_periods,
                           range_of_periods=range_of_periods,
                           order_data=order_data,
                           supplier=supplier,
                           suppliers=suppliers,
                           list_range_of_periods=list_range_of_periods,
                           start_period_range=start_period_range,
                           end_period_range=end_period_range,
                           first_period=first_period,
                           last_period=last_period)


@app.route('/pdf')
def pdf():
    cod_pl = request.args.get('cod_pl') if request.args.get('cod_pl') else 0
    i_owner = request.args.get('i_owner') if request.args.get('i_owner') else 0
    range_of_periods = request.args.get('range_of_periods')
    all_periods = request.args.get('all_periods')

    if range_of_periods or all_periods:
        periods = range_of_periods if range_of_periods else all_periods

        query_order_data = ('{' +
                            f'order(cod_pl: {cod_pl}, i_owner: {i_owner}, range_of_periods: "{periods}")' +
                            '''{cod_u for_period servicename supplier typerec_1 typerec_2 typerec_minus60
                            typerec_6 typerec_7 typerec_9 typerec_minus66 typerec_minus10 typerec_minus7 
                            typerec_minus6 typerec_minus1 total}}''')
        request_order_data = requests.post('http://192.168.1.26:8080/graphql', json={'query': query_order_data})
        order_data = (request_order_data.json())['data']
        order_data['cod_pl'] = cod_pl
        order_data['supplier'] = order_data['order'][0]['supplier']
        pprint(order_data)

        request_list_ranges_of_periods = requests.get(f'http://192.168.1.26:8080/v1/get_periods/{cod_pl}/{i_owner}')
        list_ranges_of_periods = []
        for item in json.loads(request_list_ranges_of_periods.content):
            list_ranges_of_periods.append({'start_period': (item.split('-'))[0], 'end_period': (item.split('-'))[1]})

        # query_periods = ('{' + f'owner_periods(cod_pl: {cod_pl}, i_owner: {i_owner})' + '{owner_period}}')
        # r_periods = requests.post('http://192.168.1.26:8080/graphql', json={'query': query_periods})
        # order_data['periods'] = [item['owner_period'] for item in (r_periods.json())['data']['owner_periods']]

        r_template = requests.put('http://192.168.1.26:5001/v1/pdf/7', json=order_data)
        res = make_response(r_template.content)
        res.headers.set('Content-Type', 'application/pdf')
        res.headers.set('Content-Disposition', 'inline')
        return res
    return None
