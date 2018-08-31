#!/usr/bin/env python3

from troposphere import Ref
from troposphere import Template, Parameter, Output
from troposphere import certificatemanager

template = Template("""Create the certificate for use with CloudFront.

CloudFront requires ACM certificates from us-east-1, this template
helps creating that certificate in a different region from the
main stack.

Template: certificate-template
Author: Carlos Avila <cavila@mandelbrew.com>
""")

# region Parameters
domain_name = template.add_parameter(Parameter(
    'DomainName',
    AllowedPattern=('^(([a-zA-Z]{1})|([a-zA-Z]{1}[a-zA-Z]{1})|'
                    '([a-zA-Z]{1}[0-9]{1})|([0-9]{1}[a-zA-Z]{1})|'
                    '([a-zA-Z0-9][a-zA-Z0-9-_]{1,61}[a-zA-Z0-9]))\.'
                    '([a-zA-Z]{2,6}|[a-zA-Z0-9-]{2,30}\.[a-zA-Z]{2,3})$'),
    Default='example.com',
    Description='FQDN of the site that you want to secure with the ACM certificate',
    MaxLength=100,
    MinLength=4,
    Type='String',
))

alternative_domain_names = template.add_parameter(Parameter(
    'AlternativeDomainNames',
    Default='*.example.com',
    Description='FQDNs to be included in the Subject Alternative Name extension of the ACM certificate.',
    Type='CommaDelimitedList',
))

validation_domain = template.add_parameter(Parameter(
    'ValidationDomain',
    AllowedPattern=('^(([a-zA-Z]{1})|([a-zA-Z]{1}[a-zA-Z]{1})|'
                    '([a-zA-Z]{1}[0-9]{1})|([0-9]{1}[a-zA-Z]{1})|'
                    '([a-zA-Z0-9][a-zA-Z0-9-_]{1,61}[a-zA-Z0-9]))\.'
                    '([a-zA-Z]{2,6}|[a-zA-Z0-9-]{2,30}\.[a-zA-Z]{2,3})$'),
    Default='example.com',
    Description='Domain that will be used to verify your identity.',
    Type='String',
    MaxLength=100,
    MinLength=4,
))
# endregion

# region Resources
certificate = template.add_resource(certificatemanager.Certificate(
    'Certificate',
    DomainName=Ref(domain_name),
    DomainValidationOptions=[certificatemanager.DomainValidationOption(
        DomainName=Ref(domain_name),
        ValidationDomain=Ref(validation_domain)
    )],
    SubjectAlternativeNames=Ref(alternative_domain_names),
))
# endregion

# region Outputs
template.add_output(
    Output('Certificate', Value=Ref(certificate))
)
# endregion

# region Metadata
template.add_metadata({
    'AWS::CloudFormation::Interface': {
        'ParameterLabels': {
            domain_name.title: {'default': 'Main Domain'},
            alternative_domain_names.title: {'default': 'Alt Domain'},
            validation_domain.title: {'default': 'Validation Domain'},

        },
        'ParameterGroups': [
            {
                'Label': {'default': 'Domain'},
                'Parameters': [
                    domain_name.title,
                    alternative_domain_names.title,
                    validation_domain.title,
                ]
            }
        ]
    }
})
# endregion

if __name__ == '__main__':
    print(template.to_json())
