from troposphere import Ref, GetAtt, Sub, Split, Select, Join, If
from troposphere import s3, cloudfront, codecommit

import parameters

source_bucket = s3.Bucket(
    'AppSourceBucket',
    Condition='UseSourceS3',
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
)

source_repo = codecommit.Repository(
    'AppSourceRepo',
    Condition='NotUseSourceS3',
    RepositoryName=Sub('${AWS::StackName}')
)

build = s3.Bucket(
    'AppBuild',
    WebsiteConfiguration=s3.WebsiteConfiguration(
        IndexDocument='index.html',
        ErrorDocument='404.html',
    ),
    CorsConfiguration=s3.CorsConfiguration(
        CorsRules=[
            s3.CorsRules(
                AllowedHeaders=['Authorization'],
                AllowedMethods=['GET'],
                AllowedOrigins=['*'],
                ExposedHeaders=[],
                MaxAge=3600,
            )
        ]
    )
)

build_policy = s3.BucketPolicy(
    'AppBuildPolicy',
    Bucket=Ref(build),
    PolicyDocument={
        'Statement': [
            {
                'Action': 's3:GetObject',
                'Effect': 'Allow',
                'Principal': '*',
                'Resource': [
                    Sub('${arn}/*', **{'arn': GetAtt(build, 'Arn')}),
                ]
            }
        ]
    }
)

distribution = cloudfront.Distribution(
    'AppDistribution',
    DistributionConfig=cloudfront.DistributionConfig(
        Aliases=If(
            'UseDistributionAliases',
            Split(',', Ref(parameters.aliases)),
            Ref('AWS::NoValue')
        ),
        Comment=Ref('AWS::StackName'),
        DefaultCacheBehavior=cloudfront.DefaultCacheBehavior(
            Compress=True,
            ForwardedValues=cloudfront.ForwardedValues(QueryString=True),
            TargetOriginId=GetAtt(build, 'DomainName'),
            ViewerProtocolPolicy='redirect-to-https',
        ),
        Enabled=True,
        Origins=[
            cloudfront.Origin(
                Id=GetAtt(build, 'DomainName'),
                DomainName=Select(2, Split('/', GetAtt(build, 'WebsiteURL'))),
                CustomOriginConfig=cloudfront.CustomOrigin(
                    OriginProtocolPolicy='http-only'
                ),
            ),
        ],
        PriceClass='PriceClass_100'
    ),
    Condition='CreateDistribution',
)
