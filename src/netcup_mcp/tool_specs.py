"""Tool specifications for the netcup CCP domain webservice.

Generated from the official interface description at
https://ccp.netcup.net/run/webservice/servers/endpoint.php

Each entry maps one netcup API function to its MCP tool name and JSON
schema. The four auth/session parameters (customernumber, apikey,
apipassword, apisessionid) are managed by the client, not the model, so
they are deliberately absent from every schema.
"""

from __future__ import annotations

from typing import Any

# netcup API function name -> MCP tool name (snake_case).
TOOL_NAMES: dict[str, str] = {
    'ackpoll': 'ackpoll',
    'cancelDomain': 'cancel_domain',
    'changeOwnerDomain': 'change_owner_domain',
    'createDomain': 'create_domain',
    'createHandle': 'create_handle',
    'deleteHandle': 'delete_handle',
    'getAuthcodeDomain': 'get_authcode_domain',
    'infoDnsRecords': 'info_dns_records',
    'infoDnsZone': 'info_dns_zone',
    'infoDomain': 'info_domain',
    'infoHandle': 'info_handle',
    'listallDomains': 'listall_domains',
    'listallHandle': 'listall_handle',
    'poll': 'poll',
    'priceTopleveldomain': 'price_topleveldomain',
    'transferDomain': 'transfer_domain',
    'updateDnsRecords': 'update_dns_records',
    'updateDnsZone': 'update_dns_zone',
    'updateDomain': 'update_domain',
    'updateHandle': 'update_handle',
}

TOOL_SPECS: dict[str, dict[str, Any]] = {
    'ackpoll': {'description': 'Acknowledge log message from call made via API. This function is '
                'avaliable for domain resellers.',
 'inputSchema': {'type': 'object',
                 'properties': {'apilogid': {'type': 'integer',
                                             'minimum': 1,
                                             'description': 'ID of message to mark as '
                                                            'read'},
                                'clientrequestid': {'type': 'string',
                                                    'description': 'Id from client '
                                                                   'side. Can contain '
                                                                   'letters and '
                                                                   'numbers. Field is '
                                                                   'optional'}},
                 'required': ['apilogid']}},
    'cancelDomain': {'description': 'Cancel Domain. Current Owner has to allow or deny the termination by '
                'clicking a link that is sent to him via e-mail. Process ends after 5 '
                'days if not answered. Inclusive domains that were ordered with a '
                'hosting product have to be canceled with this product. This function '
                'is avaliable for domain resellers.',
 'inputSchema': {'type': 'object',
                 'properties': {'domainname': {'type': 'string',
                                               'description': 'Name of the domain '
                                                              'including top-level '
                                                              'domain'},
                                'clientrequestid': {'type': 'string',
                                                    'description': 'Id from client '
                                                                   'side. Can contain '
                                                                   'letters and '
                                                                   'numbers. Field is '
                                                                   'optional'}},
                 'required': ['domainname']}},
    'changeOwnerDomain': {'description': 'Change Ownerhandle. Current Owner has to allow or deny the '
                'ownerchange by clicking a link that is sent to him via e-mail. '
                'Process ends after 5 days if not answered. This function is avaliable '
                'for domain resellers.',
 'inputSchema': {'type': 'object',
                 'properties': {'new_handle_id': {'type': 'integer',
                                                  'description': 'Handle ID of the '
                                                                 'contact that should '
                                                                 'be the new owner'},
                                'domainname': {'type': 'string',
                                               'description': 'Name of the domain '
                                                              'including top-level '
                                                              'domain'},
                                'clientrequestid': {'type': 'string',
                                                    'description': 'Id from client '
                                                                   'side. Can contain '
                                                                   'letters and '
                                                                   'numbers. Field is '
                                                                   'optional'}},
                 'required': ['new_handle_id', 'domainname']}},
    'createDomain': {'description': 'Create a new domain for a fee. This function is avaliable for domain '
                'resellers.',
 'inputSchema': {'type': 'object',
                 'properties': {'domainname': {'type': 'string',
                                               'description': 'Name of the domain '
                                                              'including top-level '
                                                              'domain'},
                                'contacts': {'type': 'object',
                                             'description': 'Contact handle ids per '
                                                            'contact role. Create '
                                                            'handles first with '
                                                            'create_handle.',
                                             'properties': {'ownerc': {'type': 'string',
                                                                       'description': 'Contact '
                                                                                      'handle '
                                                                                      'id.'},
                                                            'adminc': {'type': 'string',
                                                                       'description': 'Contact '
                                                                                      'handle '
                                                                                      'id.'},
                                                            'techc': {'type': 'string',
                                                                      'description': 'Contact '
                                                                                     'handle '
                                                                                     'id.'},
                                                            'zonec': {'type': 'string',
                                                                      'description': 'Contact '
                                                                                     'handle '
                                                                                     'id.'},
                                                            'billingc': {'type': 'string',
                                                                         'description': 'Contact '
                                                                                        'handle '
                                                                                        'id.'},
                                                            'onsitec': {'type': 'string',
                                                                        'description': 'Contact '
                                                                                       'handle '
                                                                                       'id.'},
                                                            'generalrequest': {'type': 'string',
                                                                               'description': 'Contact '
                                                                                              'handle '
                                                                                              'id.'},
                                                            'abusecontact': {'type': 'string',
                                                                             'description': 'Contact '
                                                                                            'handle '
                                                                                            'id.'}}},
                                'nameservers': {'type': 'object',
                                                'description': 'Nameserver assignment '
                                                               'for the zone.',
                                                'properties': {'nameserverentry': {'type': 'array',
                                                                                   'description': 'Up '
                                                                                                  'to '
                                                                                                  '8 '
                                                                                                  'nameserver '
                                                                                                  'entries.',
                                                                                   'items': {'type': 'object',
                                                                                             'properties': {'hostname': {'type': 'string',
                                                                                                                         'description': 'Nameserver '
                                                                                                                                        'hostname, '
                                                                                                                                        'e.g. '
                                                                                                                                        'ns1.example.com.'},
                                                                                                            'ipv4': {'type': 'string',
                                                                                                                     'description': 'IPv4 '
                                                                                                                                    'glue '
                                                                                                                                    'address.'},
                                                                                                            'ipv6': {'type': 'string',
                                                                                                                     'description': 'IPv6 '
                                                                                                                                    'glue '
                                                                                                                                    'address.'}},
                                                                                             'required': ['hostname']}},
                                                               'customernumber': {'type': 'integer',
                                                                                  'description': 'Customer '
                                                                                                 'number '
                                                                                                 'the '
                                                                                                 'zone '
                                                                                                 'is '
                                                                                                 'assigned '
                                                                                                 'to.'}}},
                                'clientrequestid': {'type': 'string',
                                                    'description': 'Id from client '
                                                                   'side. Can contain '
                                                                   'letters and '
                                                                   'numbers. Field is '
                                                                   'optional'}},
                 'required': ['domainname', 'contacts', 'nameservers']}},
    'createHandle': {'description': 'Create a contact handle in data base. Contact handles are mandatory '
                'for ordering domains. Fields type, name and organisation can not be '
                'changed by an update. Field email can not be changed if domain is '
                'used at a global top-level domain. This function is avaliable for '
                'domain resellers.',
 'inputSchema': {'type': 'object',
                 'properties': {'type': {'type': 'string',
                                         'description': 'type of the handle like '
                                                        'organisation or person'},
                                'name': {'type': 'string',
                                         'description': 'full name of the contact'},
                                'organisation': {'type': 'string',
                                                 'description': 'organisation like '
                                                                'company name Required '
                                                                'for organisation-type '
                                                                'handles.'},
                                'street': {'type': 'string', 'description': 'street'},
                                'postalcode': {'type': 'string',
                                               'description': 'postal code'},
                                'city': {'type': 'string', 'description': 'city'},
                                'countrycode': {'type': 'string',
                                                'description': 'countrycode in ISO '
                                                               '3166 ALPHA-2 format. 2 '
                                                               'char codes like CH for '
                                                               'Switzerland'},
                                'telephone': {'type': 'string',
                                              'description': 'telephone number'},
                                'email': {'type': 'string',
                                          'description': 'email address'},
                                'clientrequestid': {'type': 'string',
                                                    'description': 'Id from client '
                                                                   'side. Can contain '
                                                                   'letters and '
                                                                   'numbers. Field is '
                                                                   'optional'},
                                'optionalhandleattributes': {'type': 'array',
                                                             'description': 'Optional '
                                                                            'handle '
                                                                            'attributes '
                                                                            'as '
                                                                            '{"item": '
                                                                            '..., '
                                                                            '"value": '
                                                                            '...} '
                                                                            'objects.',
                                                             'items': {'type': 'object',
                                                                       'properties': {'item': {'type': 'string',
                                                                                               'description': 'Attribute '
                                                                                                              'name, '
                                                                                                              'e.g. '
                                                                                                              'state, '
                                                                                                              'handlecomment, '
                                                                                                              'birthdate, '
                                                                                                              'birthcountrycountrycode, '
                                                                                                              'taxnumber, '
                                                                                                              'vatnumber, '
                                                                                                              'esnifnienumber, '
                                                                                                              'jobswebsite.'},
                                                                                      'value': {'type': 'string',
                                                                                                'description': 'Attribute '
                                                                                                               'value.'}},
                                                                       'required': ['item',
                                                                                    'value']}}},
                 'required': ['type',
                              'name',
                              'street',
                              'postalcode',
                              'city',
                              'countrycode',
                              'telephone',
                              'email']}},
    'deleteHandle': {'description': 'Delete a contact handle in data base. You can only delete a handle in '
                'the netcup database, if it is not used with a domain. This function '
                'is avaliable for domain resellers.',
 'inputSchema': {'type': 'object',
                 'properties': {'handle_id': {'type': 'integer',
                                              'minimum': 1,
                                              'description': 'Id of the contact'},
                                'clientrequestid': {'type': 'string',
                                                    'description': 'Id from client '
                                                                   'side. Can contain '
                                                                   'letters and '
                                                                   'numbers. Field is '
                                                                   'optional'}},
                 'required': ['handle_id']}},
    'getAuthcodeDomain': {'description': 'Get auth info for domain. This function is avaliable for domain '
                'resellers.',
 'inputSchema': {'type': 'object',
                 'properties': {'domainname': {'type': 'string',
                                               'description': 'Name of the domain '
                                                              'including top-level '
                                                              'domain'},
                                'clientrequestid': {'type': 'string',
                                                    'description': 'Id from client '
                                                                   'side. Can contain '
                                                                   'letters and '
                                                                   'numbers. Field is '
                                                                   'optional'}},
                 'required': ['domainname']}},
    'infoDnsRecords': {'description': 'Get all records of a zone. Zone must be owned by customer.',
 'inputSchema': {'type': 'object',
                 'properties': {'domainname': {'type': 'string',
                                               'description': 'Name of the domain '
                                                              'including top-level '
                                                              'domain'},
                                'clientrequestid': {'type': 'string',
                                                    'description': 'Id from client '
                                                                   'side. Can contain '
                                                                   'letters and '
                                                                   'numbers. Field is '
                                                                   'optional'}},
                 'required': ['domainname']}},
    'infoDnsZone': {'description': 'Get information about dns zone in local nameservers. Zone must be '
                'owned by reseller.',
 'inputSchema': {'type': 'object',
                 'properties': {'domainname': {'type': 'string',
                                               'description': 'Name of the domain '
                                                              'including top-level '
                                                              'domain'},
                                'clientrequestid': {'type': 'string',
                                                    'description': 'Id from client '
                                                                   'side. Can contain '
                                                                   'letters and '
                                                                   'numbers. Field is '
                                                                   'optional'}},
                 'required': ['domainname']}},
    'infoDomain': {'description': 'Info Domain. Get Information about domain. All avaliable information '
                'for own domains. Status for other domains. This function is avaliable '
                'for domain resellers.',
 'inputSchema': {'type': 'object',
                 'properties': {'domainname': {'type': 'string',
                                               'description': 'Name of the domain '
                                                              'including top-level '
                                                              'domain'},
                                'clientrequestid': {'type': 'string',
                                                    'description': 'Id from client '
                                                                   'side. Can contain '
                                                                   'letters and '
                                                                   'numbers. Field is '
                                                                   'optional'},
                                'registryinformationflag': {'type': 'boolean',
                                                            'description': 'TRUE '
                                                                           'getinformation '
                                                                           'from '
                                                                           'registrymay '
                                                                           'be '
                                                                           'limited|registryinformationflag '
                                                                           'FALSE get '
                                                                           'information '
                                                                           'from '
                                                                           'netcup '
                                                                           'data base '
                                                                           'only. '
                                                                           'Field is '
                                                                           'optional. '
                                                                           'Default '
                                                                           'FALSE'}},
                 'required': ['domainname']}},
    'infoHandle': {'description': 'Get Information about a handle. This function is avaliable for domain '
                'resellers.',
 'inputSchema': {'type': 'object',
                 'properties': {'handle_id': {'type': 'integer',
                                              'minimum': 1,
                                              'description': 'Id of the contact'},
                                'clientrequestid': {'type': 'string',
                                                    'description': 'Id from client '
                                                                   'side. Can contain '
                                                                   'letters and '
                                                                   'numbers. Field is '
                                                                   'optional'}},
                 'required': ['handle_id']}},
    'listallDomains': {'description': 'Get information about all domains that a customer owns. For detailed '
                'information please use infoDomain This function is avaliable for '
                'domain resellers.',
 'inputSchema': {'type': 'object',
                 'properties': {'clientrequestid': {'type': 'string',
                                                    'description': 'Id from client '
                                                                   'side. Can contain '
                                                                   'letters and '
                                                                   'numbers. Field is '
                                                                   'optional'}},
                 'required': []}},
    'listallHandle': {'description': 'Get ids and name of all handles of a user. If Organisation is set, '
                'also value of organisation field. This function is avaliable for '
                'domain resellers.',
 'inputSchema': {'type': 'object',
                 'properties': {'clientrequestid': {'type': 'string',
                                                    'description': 'Id from client '
                                                                   'side. Can contain '
                                                                   'letters and '
                                                                   'numbers. Field is '
                                                                   'optional'}},
                 'required': []}},
    'poll': {'description': 'Get all messages that are not read. This function is avaliable for '
                'domain resellers.',
 'inputSchema': {'type': 'object',
                 'properties': {'messagecount': {'type': 'integer',
                                                 'minimum': 1,
                                                 'description': 'maximum number of '
                                                                'unread messages to '
                                                                'receive'},
                                'clientrequestid': {'type': 'string',
                                                    'description': 'Id from client '
                                                                   'side. Can contain '
                                                                   'letters and '
                                                                   'numbers. Field is '
                                                                   'optional'}},
                 'required': ['messagecount']}},
    'priceTopleveldomain': {'description': 'Get price for a top-level domain. Current discounts are considered, '
                'but can be limited by time or amount. Prices for premium domains can '
                'be higher. This function is avaliable for domain resellers. Transfers '
                'between netcup customers can result in addional costs for '
                'ownerchanges. See customer control panel.',
 'inputSchema': {'type': 'object',
                 'properties': {'topleveldomain': {'type': 'string',
                                                   'description': 'Name of the '
                                                                  'top-level domain '
                                                                  'without dot. For '
                                                                  'example de'},
                                'clientrequestid': {'type': 'string',
                                                    'description': 'Id from client '
                                                                   'side. Can contain '
                                                                   'letters and '
                                                                   'numbers. Field is '
                                                                   'optional'}},
                 'required': ['topleveldomain']}},
    'transferDomain': {'description': 'Incomming transfer a new domain for a fee. This function is avaliable '
                'for domain resellers. Transfers between netcup customers can result '
                'in addional costs for ownerchanges. See customer control panel.',
 'inputSchema': {'type': 'object',
                 'properties': {'domainname': {'type': 'string',
                                               'description': 'Name of the domain '
                                                              'including top-level '
                                                              'domain'},
                                'contacts': {'type': 'object',
                                             'description': 'Contact handle ids per '
                                                            'contact role. Create '
                                                            'handles first with '
                                                            'create_handle.',
                                             'properties': {'ownerc': {'type': 'string',
                                                                       'description': 'Contact '
                                                                                      'handle '
                                                                                      'id.'},
                                                            'adminc': {'type': 'string',
                                                                       'description': 'Contact '
                                                                                      'handle '
                                                                                      'id.'},
                                                            'techc': {'type': 'string',
                                                                      'description': 'Contact '
                                                                                     'handle '
                                                                                     'id.'},
                                                            'zonec': {'type': 'string',
                                                                      'description': 'Contact '
                                                                                     'handle '
                                                                                     'id.'},
                                                            'billingc': {'type': 'string',
                                                                         'description': 'Contact '
                                                                                        'handle '
                                                                                        'id.'},
                                                            'onsitec': {'type': 'string',
                                                                        'description': 'Contact '
                                                                                       'handle '
                                                                                       'id.'},
                                                            'generalrequest': {'type': 'string',
                                                                               'description': 'Contact '
                                                                                              'handle '
                                                                                              'id.'},
                                                            'abusecontact': {'type': 'string',
                                                                             'description': 'Contact '
                                                                                            'handle '
                                                                                            'id.'}}},
                                'nameservers': {'type': 'object',
                                                'description': 'Nameserver assignment '
                                                               'for the zone.',
                                                'properties': {'nameserverentry': {'type': 'array',
                                                                                   'description': 'Up '
                                                                                                  'to '
                                                                                                  '8 '
                                                                                                  'nameserver '
                                                                                                  'entries.',
                                                                                   'items': {'type': 'object',
                                                                                             'properties': {'hostname': {'type': 'string',
                                                                                                                         'description': 'Nameserver '
                                                                                                                                        'hostname, '
                                                                                                                                        'e.g. '
                                                                                                                                        'ns1.example.com.'},
                                                                                                            'ipv4': {'type': 'string',
                                                                                                                     'description': 'IPv4 '
                                                                                                                                    'glue '
                                                                                                                                    'address.'},
                                                                                                            'ipv6': {'type': 'string',
                                                                                                                     'description': 'IPv6 '
                                                                                                                                    'glue '
                                                                                                                                    'address.'}},
                                                                                             'required': ['hostname']}},
                                                               'customernumber': {'type': 'integer',
                                                                                  'description': 'Customer '
                                                                                                 'number '
                                                                                                 'the '
                                                                                                 'zone '
                                                                                                 'is '
                                                                                                 'assigned '
                                                                                                 'to.'}}},
                                'authcode': {'type': 'string',
                                             'description': 'AuthInfo code for this '
                                                            'domain'},
                                'clientrequestid': {'type': 'string',
                                                    'description': 'Id from client '
                                                                   'side. Can contain '
                                                                   'letters and '
                                                                   'numbers. Field is '
                                                                   'optional'}},
                 'required': ['domainname', 'contacts', 'nameservers', 'authcode']}},
    'updateDnsRecords': {'description': 'Update DNS records of a zone. Deletion of other records is optional. '
                'When DNSSEC is active, the zone is updated in the nameserver with '
                'zone resign after a few minutes.',
 'inputSchema': {'type': 'object',
                 'properties': {'domainname': {'type': 'string',
                                               'description': 'Name of the domain '
                                                              'including top-level '
                                                              'domain'},
                                'clientrequestid': {'type': 'string',
                                                    'description': 'Id from client '
                                                                   'side. Can contain '
                                                                   'letters and '
                                                                   'numbers. Field is '
                                                                   'optional'},
                                'dnsrecordset': {'type': 'object',
                                                 'description': 'The complete set of '
                                                                'DNS records for the '
                                                                'zone. Records not '
                                                                'listed are kept '
                                                                'unless you ask to '
                                                                'delete them.',
                                                 'properties': {'dnsrecords': {'type': 'array',
                                                                               'description': 'DNS '
                                                                                              'records '
                                                                                              'for '
                                                                                              'the '
                                                                                              'zone.',
                                                                               'items': {'type': 'object',
                                                                                         'properties': {'id': {'type': 'integer',
                                                                                                               'description': 'Record '
                                                                                                                              'id '
                                                                                                                              'from '
                                                                                                                              'info_dns_records. '
                                                                                                                              'Omit '
                                                                                                                              'for '
                                                                                                                              'a '
                                                                                                                              'new '
                                                                                                                              'record.'},
                                                                                                        'hostname': {'type': 'string',
                                                                                                                     'description': 'Record '
                                                                                                                                    'hostname. '
                                                                                                                                    'Use '
                                                                                                                                    '@ '
                                                                                                                                    'for '
                                                                                                                                    'the '
                                                                                                                                    'zone '
                                                                                                                                    'apex.'},
                                                                                                        'type': {'type': 'string',
                                                                                                                 'enum': ['A',
                                                                                                                          'AAAA',
                                                                                                                          'MX',
                                                                                                                          'TXT',
                                                                                                                          'CNAME',
                                                                                                                          'NS',
                                                                                                                          'SRV',
                                                                                                                          'CAA',
                                                                                                                          'NAPTR',
                                                                                                                          'TLSA',
                                                                                                                          'SSHFP',
                                                                                                                          'DS',
                                                                                                                          'DNSKEY',
                                                                                                                          'SOA',
                                                                                                                          'SPF',
                                                                                                                          'URI'],
                                                                                                                 'description': 'Record '
                                                                                                                                'type. '
                                                                                                                                'Use '
                                                                                                                                '@ '
                                                                                                                                'for '
                                                                                                                                'the '
                                                                                                                                'zone '
                                                                                                                                'apex '
                                                                                                                                'hostname.'},
                                                                                                        'priority': {'type': 'string',
                                                                                                                     'description': 'Priority, '
                                                                                                                                    'required '
                                                                                                                                    'for '
                                                                                                                                    'MX '
                                                                                                                                    'and '
                                                                                                                                    'SRV '
                                                                                                                                    'records.'},
                                                                                                        'destination': {'type': 'string',
                                                                                                                        'description': 'Record '
                                                                                                                                       'target, '
                                                                                                                                       'e.g. '
                                                                                                                                       'an '
                                                                                                                                       'IP '
                                                                                                                                       'address '
                                                                                                                                       'or '
                                                                                                                                       'hostname.'},
                                                                                                        'deleterecord': {'type': 'boolean',
                                                                                                                         'description': 'Set '
                                                                                                                                        'true '
                                                                                                                                        'to '
                                                                                                                                        'delete '
                                                                                                                                        'this '
                                                                                                                                        'record.'}},
                                                                                         'required': ['hostname',
                                                                                                      'type',
                                                                                                      'destination']}}}}},
                 'required': ['domainname', 'dnsrecordset']}},
    'updateDnsZone': {'description': 'Update DNS zone. When DNSSEC is active, the zone is updated in the '
                'nameserver with zone resign after a few minutes.',
 'inputSchema': {'type': 'object',
                 'properties': {'domainname': {'type': 'string',
                                               'description': 'Name of the domain '
                                                              'including top-level '
                                                              'domain'},
                                'clientrequestid': {'type': 'string',
                                                    'description': 'Id from client '
                                                                   'side. Can contain '
                                                                   'letters and '
                                                                   'numbers. Field is '
                                                                   'optional'},
                                'dnszone': {'type': 'object',
                                            'description': 'DNS zone settings.',
                                            'properties': {'name': {'type': 'string',
                                                                    'description': 'Zone '
                                                                                   'name, '
                                                                                   'the '
                                                                                   'domain '
                                                                                   'name.'},
                                                           'ttl': {'type': 'integer',
                                                                   'description': 'Time '
                                                                                  'to '
                                                                                  'live '
                                                                                  'in '
                                                                                  'seconds. '
                                                                                  'Recommendation: '
                                                                                  '3600 '
                                                                                  'to '
                                                                                  '172800.'},
                                                           'refresh': {'type': 'integer',
                                                                       'description': 'Seconds '
                                                                                      'a '
                                                                                      'secondary '
                                                                                      'server '
                                                                                      'waits '
                                                                                      'before '
                                                                                      'checking '
                                                                                      'for '
                                                                                      'an '
                                                                                      'update. '
                                                                                      'Recommendation: '
                                                                                      '3600 '
                                                                                      'to '
                                                                                      '14400.'},
                                                           'retry': {'type': 'integer',
                                                                     'description': 'Seconds '
                                                                                    'to '
                                                                                    'wait '
                                                                                    'after '
                                                                                    'a '
                                                                                    'failed '
                                                                                    'refresh. '
                                                                                    'Recommendation: '
                                                                                    '900 '
                                                                                    'to '
                                                                                    '3600.'},
                                                           'expire': {'type': 'integer',
                                                                      'description': 'Seconds '
                                                                                     'a '
                                                                                     'secondary '
                                                                                     'server '
                                                                                     'holds '
                                                                                     'the '
                                                                                     'zone. '
                                                                                     'Recommendation: '
                                                                                     '592200 '
                                                                                     'to '
                                                                                     '1776600.'},
                                                           'dnssecstatus': {'type': 'string',
                                                                            'description': 'DNSSEC '
                                                                                           'status '
                                                                                           'of '
                                                                                           'the '
                                                                                           'zone.'}}}},
                 'required': ['domainname', 'dnszone']}},
    'updateDomain': {'description': 'Update a domain contacts and nameserver settings. For updateing owner '
                'handle use changeOwnerDomain. This function is avaliable for domain '
                'resellers.',
 'inputSchema': {'type': 'object',
                 'properties': {'domainname': {'type': 'string',
                                               'description': 'Name of the domain '
                                                              'including top-level '
                                                              'domain'},
                                'contacts': {'type': 'object',
                                             'description': 'Contact handle ids per '
                                                            'contact role. Create '
                                                            'handles first with '
                                                            'create_handle.',
                                             'properties': {'ownerc': {'type': 'string',
                                                                       'description': 'Contact '
                                                                                      'handle '
                                                                                      'id.'},
                                                            'adminc': {'type': 'string',
                                                                       'description': 'Contact '
                                                                                      'handle '
                                                                                      'id.'},
                                                            'techc': {'type': 'string',
                                                                      'description': 'Contact '
                                                                                     'handle '
                                                                                     'id.'},
                                                            'zonec': {'type': 'string',
                                                                      'description': 'Contact '
                                                                                     'handle '
                                                                                     'id.'},
                                                            'billingc': {'type': 'string',
                                                                         'description': 'Contact '
                                                                                        'handle '
                                                                                        'id.'},
                                                            'onsitec': {'type': 'string',
                                                                        'description': 'Contact '
                                                                                       'handle '
                                                                                       'id.'},
                                                            'generalrequest': {'type': 'string',
                                                                               'description': 'Contact '
                                                                                              'handle '
                                                                                              'id.'},
                                                            'abusecontact': {'type': 'string',
                                                                             'description': 'Contact '
                                                                                            'handle '
                                                                                            'id.'}}},
                                'nameservers': {'type': 'object',
                                                'description': 'Nameserver assignment '
                                                               'for the zone.',
                                                'properties': {'nameserverentry': {'type': 'array',
                                                                                   'description': 'Up '
                                                                                                  'to '
                                                                                                  '8 '
                                                                                                  'nameserver '
                                                                                                  'entries.',
                                                                                   'items': {'type': 'object',
                                                                                             'properties': {'hostname': {'type': 'string',
                                                                                                                         'description': 'Nameserver '
                                                                                                                                        'hostname, '
                                                                                                                                        'e.g. '
                                                                                                                                        'ns1.example.com.'},
                                                                                                            'ipv4': {'type': 'string',
                                                                                                                     'description': 'IPv4 '
                                                                                                                                    'glue '
                                                                                                                                    'address.'},
                                                                                                            'ipv6': {'type': 'string',
                                                                                                                     'description': 'IPv6 '
                                                                                                                                    'glue '
                                                                                                                                    'address.'}},
                                                                                             'required': ['hostname']}},
                                                               'customernumber': {'type': 'integer',
                                                                                  'description': 'Customer '
                                                                                                 'number '
                                                                                                 'the '
                                                                                                 'zone '
                                                                                                 'is '
                                                                                                 'assigned '
                                                                                                 'to.'}}},
                                'clientrequestid': {'type': 'string',
                                                    'description': 'Id from client '
                                                                   'side. Can contain '
                                                                   'letters and '
                                                                   'numbers. Field is '
                                                                   'optional'},
                                'keepdnssecrecords': {'type': 'boolean',
                                                      'description': 'TRUE Saved '
                                                                     'DNSSEC records '
                                                                     'will be '
                                                                     'preserved|keepdnssecrecords '
                                                                     'FALSE Saved '
                                                                     'DNSSEC records '
                                                                     'will be deleted. '
                                                                     'Information is '
                                                                     'only relevant if '
                                                                     'you use DNSSEC. '
                                                                     'Field is '
                                                                     'optional. '
                                                                     'Default FALSE'},
                                'dnssecentries': {'type': 'object',
                                                  'description': 'DNSSEC entries keyed '
                                                                 'dnssecentry1 to '
                                                                 'dnssecentry14, each '
                                                                 'a Dnssec entry '
                                                                 'object.',
                                                  'additionalProperties': True}},
                 'required': ['domainname', 'contacts', 'nameservers']}},
    'updateHandle': {'description': 'Update a existing contact handle in data base and at registries where '
                'it is used. Handle is created at a registry as soon as it is used. '
                'This function is avaliable for domain resellers.',
 'inputSchema': {'type': 'object',
                 'properties': {'handle_id': {'type': 'integer',
                                              'minimum': 1,
                                              'description': 'Id of the contact that '
                                                             'will be updated'},
                                'type': {'type': 'string',
                                         'description': 'type of the handle like '
                                                        'organisation or person'},
                                'name': {'type': 'string',
                                         'description': 'full name of the contact'},
                                'organisation': {'type': 'string',
                                                 'description': 'organisation like '
                                                                'company name Required '
                                                                'for organisation-type '
                                                                'handles.'},
                                'street': {'type': 'string', 'description': 'street'},
                                'postalcode': {'type': 'string',
                                               'description': 'postcode'},
                                'city': {'type': 'string', 'description': 'city'},
                                'countrycode': {'type': 'string',
                                                'description': 'countrycode in ISO '
                                                               '3166 ALPHA-2 format. 2 '
                                                               'char codes like CH for '
                                                               'Switzerland'},
                                'telephone': {'type': 'string',
                                              'description': 'telephone number'},
                                'email': {'type': 'string',
                                          'description': 'email address'},
                                'clientrequestid': {'type': 'string',
                                                    'description': 'Id from client '
                                                                   'side. Can contain '
                                                                   'letters and '
                                                                   'numbers. Field is '
                                                                   'optional'},
                                'optionalhandleattributes': {'type': 'array',
                                                             'description': 'Optional '
                                                                            'handle '
                                                                            'attributes '
                                                                            'as '
                                                                            '{"item": '
                                                                            '..., '
                                                                            '"value": '
                                                                            '...} '
                                                                            'objects.',
                                                             'items': {'type': 'object',
                                                                       'properties': {'item': {'type': 'string',
                                                                                               'description': 'Attribute '
                                                                                                              'name, '
                                                                                                              'e.g. '
                                                                                                              'state, '
                                                                                                              'handlecomment, '
                                                                                                              'birthdate, '
                                                                                                              'birthcountrycountrycode, '
                                                                                                              'taxnumber, '
                                                                                                              'vatnumber, '
                                                                                                              'esnifnienumber, '
                                                                                                              'jobswebsite.'},
                                                                                      'value': {'type': 'string',
                                                                                                'description': 'Attribute '
                                                                                                               'value.'}},
                                                                       'required': ['item',
                                                                                    'value']}}},
                 'required': ['handle_id',
                              'type',
                              'name',
                              'street',
                              'postalcode',
                              'city',
                              'countrycode',
                              'telephone',
                              'email']}},
}
