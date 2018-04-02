from secrets import ET_API_KEY
doc= {
    'name': 'et_hash_dns',
    'id': 'hash',
    'inputs': {
        'name': 'et_hash_dns_input',
        'type': 'REST',
        'location' : {
            'url': lambda args: "https://api.emergingthreats.net/v1/samples/{}/dns".format(args.get('hash')),
            'headers': {
                'Authorization': ET_API_KEY,
            },
        },
        'data': {
            'REMAP': {
                'et_dns_addresses' : ('response', lambda li: [ v for dic in li for k,v in dic.items() if k == 'address'] )
            },
        },
    },
    'cache': None,
}
