#!/usr/bin/env python3

from troposphere import Ref, GetAtt, Join, Sub
from troposphere import Template, Parameter, Output
from troposphere import cloudfront, s3

# Magic AWS number For CloudFront
CLOUDFRONT_HOSTED_ZONE_ID = 'Z2FDTNDATAQYW2'

template = Template("""Provide static and media content distribution using CloudFront for a Django application. It 
assumes there's separate buckets for static and media assets. Always forward http to https.

Creates the following resources:
    - CloudFront distribution

Template: cdn-template.
Author: Carlos Avila <cavila@mandelbrew.com>.
""")

# region Resources
source = template.add_resource(s3.Bucket(
    'AppSource',
    VersioningConfiguration=s3.VersioningConfiguration(Status='Enabled'),
    LifecycleConfiguration=s3.LifecycleConfiguration(
        Rules=[
            s3.LifecycleRule(
                AbortIncompleteMultipartUpload=s3.AbortIncompleteMultipartUpload(DaysAfterInitiation=3),
                Id='History Limit',
                NoncurrentVersionExpirationInDays=7,
                Status='Enabled',
            )
        ]
    )
))

static = template.add_resource(s3.Bucket(
    'AppStatic',
    CorsConfiguration=s3.CorsConfiguration(
        CorsRules=[
            s3.CorsRules(
                AllowedHeaders=['Authorization'],
                AllowedMethods=['GET', 'HEAD'],
                AllowedOrigins=['*'],
                ExposedHeaders=[],
                MaxAge=3600,
            )
        ]
    )
))

oai = template.add_resource(cloudfront.CloudFrontOriginAccessIdentity(
    'AppDistributionOai',
    CloudFrontOriginAccessIdentityConfig=cloudfront.CloudFrontOriginAccessIdentityConfig(
        Comment=Ref(static)
    )
))

distribution = template.add_resource(cloudfront.Distribution(
    'Distribution',
    DistributionConfig=cloudfront.DistributionConfig(
        Comment=Ref('AWS::StackName'),
        DefaultCacheBehavior=cloudfront.DefaultCacheBehavior(
            AllowedMethods=['GET', 'HEAD', 'OPTIONS'],
            Compress=True,
            TargetOriginId=GetAtt(static, 'DomainName'),
            ViewerProtocolPolicy='allow-all',
            ForwardedValues=cloudfront.ForwardedValues(
                Headers=['Access-Control-Request-Headers', 'Access-Control-Request-Method', 'Origin'],
                QueryString=False
            ),
        ),
        Enabled=True,
        Origins=[
            cloudfront.Origin(
                Id=GetAtt(static, 'DomainName'),
                DomainName=GetAtt(static, 'DomainName'),
                S3OriginConfig=cloudfront.S3Origin(
                    OriginAccessIdentity=Join('/', ['origin-access-identity', 'cloudfront', Ref(oai)])
                ),
            ),
        ],
        PriceClass='PriceClass_100'
    )
))

static_policy = template.add_resource(s3.BucketPolicy(
    'AppStaticPolicy',
    Bucket=Ref(static),
    PolicyDocument={
        'Statement': [
            {
                'Action': ['s3:GetObject'],
                'Effect': 'Allow',
                'Principal': {
                    'CanonicalUser': GetAtt(oai, 'S3CanonicalUserId'),
                },
                'Resource': [
                    Sub('${arn}/*', **{'arn': GetAtt(static, 'Arn')}),
                ]
            }
        ]
    }
))
# endregion

# region Outputs
template.add_output(Output(
    'Distribution',
    Value=Ref(distribution)
))
# endregion

if __name__ == '__main__':
    print(template.to_json())
