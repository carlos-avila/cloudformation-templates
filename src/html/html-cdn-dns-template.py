#!/usr/bin/env python3

from troposphere import Ref, GetAtt, Sub
from troposphere import Equals, Condition, Not, And, If
from troposphere import Template, Parameter, Output
from troposphere import route53, cloudfront, certificatemanager

# Magic AWS number:  For CloudFront, use Z2FDTNDATAQYW2.
CLOUDFRONT_HOSTED_ZONE_ID = 'Z2FDTNDATAQYW2'

template = Template("""Provide content distribution with automatic SSL and DNS management.

Creates the following resources:
    - CloudFront distribution: distributes contents of any single origin.
    - ACM certificate: allows SSL authentication. 
    - Route53 record set: for up to two domains. A main domain and an alternate.
    
Goes well with:
    - html-s3-ci

Template: html-cdn-dns.
Author: Carlos Avila <cavila@mandelbrew.com>.
""")

# region Parameters
alternative_domain = template.add_parameter(Parameter(
    'AlternativeDomain',
    AllowedPattern=('^((([a-zA-Z]{1})|([a-zA-Z]{1}[a-zA-Z]{1})|'
                    '([a-zA-Z]{1}[0-9]{1})|([0-9]{1}[a-zA-Z]{1})|'
                    '([a-zA-Z0-9][a-zA-Z0-9-_]{1,61}[a-zA-Z0-9]))\.'
                    '([a-zA-Z]{2,6}|[a-zA-Z0-9-]{2,30}\.[a-zA-Z]{2,3}))*$'),
    Default='www.example.com',
    Description='Optional. Domain name used to configure CloudFront and Route53.',
    Type='String'
))

main_domain = template.add_parameter(Parameter(
    'MainDomain',
    AllowedPattern=('^(([a-zA-Z]{1})|([a-zA-Z]{1}[a-zA-Z]{1})|'
                    '([a-zA-Z]{1}[0-9]{1})|([0-9]{1}[a-zA-Z]{1})|'
                    '([a-zA-Z0-9][a-zA-Z0-9-_]{1,61}[a-zA-Z0-9]))\.'
                    '([a-zA-Z]{2,6}|[a-zA-Z0-9-]{2,30}\.[a-zA-Z]{2,3})$'),
    Default='example.com',
    Description='Domain name used to configure CloudFront and Route53.',
    Type='String'
))

hosted_zone_id = template.add_parameter(Parameter(
    'HostedZoneId',
    Description='Hosted zone used for domain name.',
    Type='AWS::Route53::HostedZone::Id'
))

origin_domain = template.add_parameter(Parameter(
    'OriginDomain',
    Default='myapp-bucket-name.s3-website-us-east-1.amazonaws.com',
    Description='S3 bucket name or web URL',
    Type='String'
))

origin_path = template.add_parameter(Parameter(
    'OriginPath',
    Default='',
    Description='If you want CloudFront to request your content from a directory, enter the directory name here, '
                'beginning with a /. Do not include a / at the end of the directory name.',
    Type='String'
))

price_class = template.add_parameter(Parameter(
    'PriceClass',
    AllowedValues=['PriceClass_100', 'PriceClass_200', 'PriceClass_All'],
    Default='PriceClass_100',
    Description='The price class that corresponds with the maximum price that you want to pay for the CloudFront '
                'service.',
    Type='String'
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
))

# endregion

# region Conditions
has_main_domain = template.add_condition(
    'HasMainDomain',
    Not(Equals(Ref(main_domain), ''))
)
has_hosted_zone = template.add_condition(
    'HasHostedZone',
    Not(Equals(Ref(hosted_zone_id), ''))
)
has_alt_domain = template.add_condition(
    'HasAlternativeDomain',
    Not(Equals(Ref(alternative_domain), ''))
)
has_main_and_alt_domain = template.add_condition(
    'HasMainAndAltDomain',
    And(
        Condition(has_main_domain),
        Condition(has_alt_domain),
    )
)
# endregion

# region Resources
certificate = template.add_resource(certificatemanager.Certificate(
    'Certificate',
    DomainName=Ref(main_domain),
    DomainValidationOptions=[certificatemanager.DomainValidationOption(
        DomainName=Ref(main_domain),
        ValidationDomain=Ref(validation_domain)
    )],
    SubjectAlternativeNames=If(has_main_and_alt_domain, [Ref(alternative_domain)], [Ref('AWS::NoValue')]),
))

distribution = template.add_resource(cloudfront.Distribution(
    'Distribution',
    DistributionConfig=cloudfront.DistributionConfig(
        Aliases=If(has_main_and_alt_domain, [Ref(main_domain), Ref(alternative_domain)], [Ref(main_domain)]),
        Comment=Ref('AWS::StackName'),
        DefaultCacheBehavior=cloudfront.DefaultCacheBehavior(
            Compress=True,
            ForwardedValues=cloudfront.ForwardedValues(QueryString=True),
            TargetOriginId=Sub('${domain}${path}', **{
                'domain': Ref(origin_domain),
                'path': Ref(origin_path)
            }),
            ViewerProtocolPolicy='redirect-to-https',
        ),
        Enabled=True,
        Origins=[
            cloudfront.Origin(
                Id=Sub('${domain}${path}', **{
                    'domain': Ref(origin_domain),
                    'path': Ref(origin_path)
                }),
                DomainName=Ref(origin_domain),
                OriginPath=Ref(origin_path),
                CustomOriginConfig=cloudfront.CustomOrigin(
                    OriginProtocolPolicy='http-only'
                ),
            ),
        ],
        PriceClass=Ref(price_class),
        ViewerCertificate=cloudfront.ViewerCertificate(
            AcmCertificateArn=Ref(certificate),
            SslSupportMethod='sni-only',
        ),
    ),
))

record_set_group = template.add_resource(route53.RecordSetGroup(
    'RecordSetGroup',
    Comment=Ref('AWS::StackName'),
    HostedZoneId=Ref(hosted_zone_id),
    RecordSets=[
        route53.RecordSet(
            AliasTarget=route53.AliasTarget(
                HostedZoneId=CLOUDFRONT_HOSTED_ZONE_ID,
                DNSName=GetAtt(distribution, 'DomainName'),
            ),
            Name=Ref(main_domain),
            Type='A',
        ),
        If(
            has_alt_domain,
            route53.RecordSet(
                AliasTarget=route53.AliasTarget(
                    HostedZoneId=CLOUDFRONT_HOSTED_ZONE_ID,
                    DNSName=GetAtt(distribution, 'DomainName'),
                ),
                Name=Ref(alternative_domain),
                Type='A',
            ),
            Ref('AWS::NoValue')
        ),
    ]
))

# endregion

# region Outputs
distribution_domain_name = template.add_output(Output(
    'DistributionDomainName',
    Value=GetAtt(distribution, 'DomainName')
))
# endregion

# region Metadata
template.add_metadata({
    'AWS::CloudFormation::Interface': {
        'ParameterLabels': {
            # Cert
            validation_domain.title: {'default': 'Validation Domain'},
            # DNS
            hosted_zone_id.title: {'default': 'Hosted Zone ID'},
            main_domain.title: {'default': 'Main Domain'},
            alternative_domain.title: {'default': 'Alternate Domain'},
            # CDN
            origin_domain.title: {'default': 'Origin Domain'},
            origin_path.title: {'default': 'Origin Path'},
            price_class.title: {'default': 'Price Class'},
        },
        'ParameterGroups': [
            {
                'Label': {'default': 'Certificate'},
                'Parameters': [
                    validation_domain.title,
                ]
            },
            {
                'Label': {'default': 'DNS'},
                'Parameters': [
                    hosted_zone_id.title,
                    main_domain.title,
                    alternative_domain.title,
                ]
            },
            {
                'Label': {'default': 'CDN'},
                'Parameters': [
                    origin_domain.title,
                    origin_path.title,
                    price_class.title,
                ]
            },
        ]
    }
})
# endregion

if __name__ == '__main__':
    print(template.to_json())
