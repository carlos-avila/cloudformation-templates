#!/usr/bin/env python3

from troposphere import Ref, Sub, GetAtt
from troposphere import Template, Parameter, Output
from troposphere import cloudfront, route53

# Magic AWS number For CloudFront
CLOUDFRONT_HOSTED_ZONE_ID = 'Z2FDTNDATAQYW2'

template = Template("""Provide static and media content distribution using CloudFront for a Django application. 
Route53 provides an A record to access the CDN through a custom domain. It assumes there's separate buckets for 
static and media assets. Always forward http to https. Please note CloudFront requires ACM certificates be created in 
us-east-1. 

Creates the following resources:
- CloudFront distribution
- Route53 record set

Template: cdn-cname-template.
Author: Carlos Avila <cavila@mandelbrew.com>.
""")

# region Parameters
hosted_zone_id = template.add_parameter(Parameter(
    'HostedZoneId',
    Description='Hosted zone used for the CDN domain name.',
    Type='AWS::Route53::HostedZone::Id'
))

domain = template.add_parameter(Parameter(
    'Domain',
    Default='cdn.example.com',
    Description='CNAME for the distribution.',
    Type='String',
))

certificate = template.add_parameter(Parameter(
    'Certificate',
    Description='ARN of the ACM certificate used for Cloudfront\'s SSL',
    Type='String'
))

static_domain = template.add_parameter(Parameter(
    'StaticDomain',
    Default='myapp-static-assets.s3.amazonaws.com',
    Description='S3 bucket storing static assets',
    Type='String'
))

static_path = template.add_parameter(Parameter(
    'StaticPath',
    Default='',
    Description='If you want CloudFront to request your content from a directory, enter the directory name here, '
                'beginning with a /. Do not include a / at the end of the directory name.',
    Type='String'
))

media_domain = template.add_parameter(Parameter(
    'MediaDomain',
    Default='myapp-media-assets.s3.amazonaws.com',
    Description='S3 bucket storing media assets',
    Type='String'
))

media_path = template.add_parameter(Parameter(
    'MediaPath',
    Default='',
    Description='If you want CloudFront to request your content from a directory, enter the directory name here, '
                'beginning with a /. Do not include a / at the end of the directory name.',
    Type='String'
))

media_pattern = template.add_parameter(Parameter(
    'MediaPattern',
    Default='/media/*',
    Description='Specify which requests you want to route to the origin.',
    Type='String'
))
# endregion

# region Resources
distribution = template.add_resource(cloudfront.Distribution(
    'Distribution',
    DistributionConfig=cloudfront.DistributionConfig(
        Aliases=[Ref(domain)],
        CacheBehaviors=[
            cloudfront.CacheBehavior(
                Compress=True,
                ForwardedValues=cloudfront.ForwardedValues(
                    Cookies=cloudfront.Cookies(Forward='none'),
                    QueryString=False,
                ),
                PathPattern=Ref(media_pattern),
                TargetOriginId=Sub('${domain}${path}', **{
                    'domain': Ref(media_domain),
                    'path': Ref(media_path)
                }),
                ViewerProtocolPolicy='redirect-to-https',
            )
        ],
        Comment=Sub('${AWS::StackName}'),
        DefaultCacheBehavior=cloudfront.DefaultCacheBehavior(
            Compress=True,
            ForwardedValues=cloudfront.ForwardedValues(
                Cookies=cloudfront.Cookies(Forward='none'),
                QueryString=False,
            ),
            TargetOriginId=Sub('${domain}${path}', **{
                'domain': Ref(static_domain),
                'path': Ref(static_path)
            }),
            ViewerProtocolPolicy='redirect-to-https',
        ),
        Enabled=True,
        Origins=[
            cloudfront.Origin(
                Id=Sub('${domain}${path}', **{
                    'domain': Ref(static_domain),
                    'path': Ref(static_path)
                }),
                DomainName=Ref(static_domain),
                OriginPath=Ref(static_path),
                CustomOriginConfig=cloudfront.CustomOrigin(
                    OriginProtocolPolicy='https-only'
                ),
            ),
            cloudfront.Origin(
                Id=Sub('${domain}${path}', **{
                    'domain': Ref(media_domain),
                    'path': Ref(media_path)
                }),
                DomainName=Ref(media_domain),
                OriginPath=Ref(media_path),
                CustomOriginConfig=cloudfront.CustomOrigin(
                    OriginProtocolPolicy='https-only'
                ),
            ),
        ],
        PriceClass='PriceClass_100',
        ViewerCertificate=cloudfront.ViewerCertificate(
            AcmCertificateArn=Ref(certificate),
            SslSupportMethod='sni-only',
        )
    )
))

record_set_group = template.add_resource(route53.RecordSetGroup(
    'RecordSetGroup',
    HostedZoneId=Ref(hosted_zone_id),
    RecordSets=[
        route53.RecordSet(
            Name=Ref(domain),
            Type='A',
            AliasTarget=route53.AliasTarget(
                HostedZoneId=CLOUDFRONT_HOSTED_ZONE_ID,
                DNSName=GetAtt(distribution, 'DomainName'),
            )
        ),
    ]
))
# endregion

# region Outputs
template.add_output(Output(
    'Distribution',
    Value=Ref(distribution)
))
# endregion

# region Metadata
template.add_metadata({
    'AWS::CloudFormation::Interface': {
        'ParameterLabels': {
            # Django CDN
            hosted_zone_id.title: {'default': 'Hosted Zone ID'},
            domain.title: {'default': 'Domain'},
            certificate.title: {'default': 'ACM certificate'},
            # Static assets CDN
            static_domain.title: {'default': 'Static Domain Name'},
            static_path.title: {'default': 'Static Path'},
            # Media assets CDN
            media_domain.title: {'default': 'Media Domain Name'},
            media_path.title: {'default': 'Media Path'},
            media_pattern.title: {'default': 'Media Pattern'},
        },
        'ParameterGroups': [
            {
                'Label': {'default': 'Django CDN'},
                'Parameters': [
                    hosted_zone_id.title,
                    domain.title,
                    certificate.title,
                ]
            },
            {
                'Label': {'default': 'Static Assets CDN'},
                'Parameters': [
                    static_domain.title,
                    static_path.title,
                ]
            },
            {
                'Label': {'default': 'Media Assets CDN'},
                'Parameters': [
                    media_domain.title,
                    media_path.title,
                    media_pattern.title,
                ]
            },
        ]
    }
})
# endregion

if __name__ == '__main__':
    print(template.to_json())
