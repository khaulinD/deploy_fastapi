PERMISSION = {
'admin': [
        {
            'type': 'CREATE', 'record_type': 'Doctor', 'condition': True
        }
    ],
    'company': [
        {
            'type': 'UPDATE', 'record_type': 'company', 'condition': True
        },
        {
            'type': 'READ', 'record_type': 'company/user', 'condition': True
        },
        {
            'type': 'CREATE', 'record_type': 'company/user', 'condition': True
        },
        {
            'type': 'DELETE', 'record_type': 'company/user', 'condition': True
        },
        {
            'type': 'UPDATE', 'record_type': 'company/user', 'condition': True
        },
        {
            'type': 'CREATE', 'record_type': 'user_tariff', 'condition': True
        },
        {
            'type': 'READ', 'record_type': 'user_tariff', 'condition': True
        },
        {
            'type': 'READ', 'record_type': 'payment', 'condition': True
        },
        {
            'type': 'CREATE', 'record_type': 'payment', 'condition': True
        },
        {
            'type': 'READ', 'record_type': 'checkout_auth', 'condition': True
        },
        {
            'type': 'READ', 'record_type': 'notes', 'condition': True
        },

    ],
    'user': [
        {
            'type': 'READ', 'record_type': 'user', 'condition': True
        },
        {
            'type': 'CREATE', 'record_type': 'user', 'condition': True
        },
        {
            'type': 'UPDATE', 'record_type': 'user', 'condition': True
        },
        {
            'type': 'READ', 'record_type': 'notes', 'condition': True
        },
        {
            'type': 'UPDATE', 'record_type': 'notes', 'condition': True
        },
        {
            'type': 'DELETE', 'record_type': 'notes', 'condition': True
        },
        {
            'type': 'READ', 'record_type': 'payment', 'condition': True
        },
        {
            'type': 'CREATE', 'record_type': 'payment', 'condition': True
        }
    ],
    'companyuser': [
        {
            'type': 'UPDATE', 'record_type': 'company/user', 'condition': True
        },
        {
            'type': 'READ', 'record_type': 'checkout_auth', 'condition': True
        },
        {
            'type': 'CREATE', 'record_type': 'notes', 'condition': True
        },
        {
            'type': 'READ', 'record_type': 'notes', 'condition': True
        },
        {
            'type': 'UPDATE', 'record_type': 'notes', 'condition': True
        },
        {
            'type': 'DELETE', 'record_type': 'notes', 'condition': True
        },
    ]
}

METHODS = {
    'GET': 'READ',
    'POST': 'CREATE',
    'PUT': 'UPDATE',
    'PATCH': 'UPDATE',
    'DELETE': 'DELETE',
}

#Type of url of permission check
ACTIONS = ['company/user', 'user_tariff', 'company', 'tariff_plan', 'notes', 'payment', "checkout_auth"]

#Type of ulr for tariff plan check
TARIFF_URL = {('company/doctor', "POST"),
              ('notes', "GET"),
              # ('notes_generate', "POST")
              }


async def get_method(method):
    return METHODS[method]


async def get_action(url):
    for e in ACTIONS:
        if e in url:
            return e

    return None


async def get_tariff_url(url, method):
    for e in TARIFF_URL:
        if e[0] in url and e[1] == method:
            return e
    return None
