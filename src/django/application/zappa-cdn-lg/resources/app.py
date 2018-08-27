from troposphere import Ref, Sub, GetAtt
from troposphere import s3, iam, cloudfront, codecommit

role = iam.Role(
    'AppRole',
    AssumeRolePolicyDocument={
        'Statement': [
            {
                'Action': 'sts:AssumeRole',
                'Effect': 'Allow',
                'Principal': {
                    'Service': [
                        'apigateway.amazonaws.com',
                        'events.amazonaws.com',
                        'lambda.amazonaws.com',
                    ]
                }
            }
        ]
    }
)

secrets = s3.Bucket(
    'AppSecrets',
    VersioningConfiguration=s3.VersioningConfiguration(Status='Enabled'),
)
source = s3.Bucket(
    'AppSource',
)

static_assets = s3.Bucket(
    'AppStaticAssets',
    CorsConfiguration=s3.CorsConfiguration(
        CorsRules=[
            s3.CorsRules(
                AllowedHeaders=['Authorization'],
                AllowedMethods=['GET'],
                AllowedOrigins=['*'],
                ExposedHeaders=[],
                MaxAge=3000,
            )
        ]
    )
)

static_assets_policy = s3.BucketPolicy(
    'AppStaticAssetsPolicy',
    Bucket=Ref(static_assets),
    PolicyDocument={
        'Statement': [
            {
                'Action': 's3:GetObject',
                'Effect': 'Allow',
                'Principal': '*',
                'Resource': [
                    Sub('${arn}/*', **{'arn': GetAtt(static_assets, 'Arn')}),
                ]
            },

        ]
    }
)

media_assets = s3.Bucket(
    'AppMediaAssets',
    CorsConfiguration=s3.CorsConfiguration(
        CorsRules=[
            s3.CorsRules(
                AllowedHeaders=['Authorization'],
                AllowedMethods=['GET'],
                AllowedOrigins=['*'],
                ExposedHeaders=[],
                MaxAge=3000,
            )
        ]
    )
)

media_assets_policy = s3.BucketPolicy(
    'AppMediaAssetsPolicy',
    Bucket=Ref(media_assets),
    PolicyDocument={
        'Statement': [
            {
                'Action': 's3:GetObject',
                'Effect': 'Allow',
                'Principal': '*',
                'Resource': [
                    Sub('${arn}/*', **{'arn': GetAtt(media_assets, 'Arn')}),
                ]
            }
        ]
    }
)

distribution = cloudfront.Distribution(
    'AppDistribution',
    DistributionConfig=cloudfront.DistributionConfig(
        CacheBehaviors=[
            cloudfront.CacheBehavior(
                Compress=True,
                ForwardedValues=cloudfront.ForwardedValues(
                    Cookies=cloudfront.Cookies(Forward='none'),
                    QueryString=False,
                ),
                PathPattern='/media/*',
                TargetOriginId=GetAtt(media_assets, 'DomainName'),
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
            TargetOriginId=GetAtt(static_assets, 'DomainName'),
            ViewerProtocolPolicy='redirect-to-https',
        ),
        Enabled=True,
        Origins=[
            cloudfront.Origin(
                Id=GetAtt(static_assets, 'DomainName'),
                DomainName=GetAtt(static_assets, 'DomainName'),
                CustomOriginConfig=cloudfront.CustomOrigin(
                    OriginProtocolPolicy='https-only'
                ),
            ),
            cloudfront.Origin(
                Id=GetAtt(media_assets, 'DomainName'),
                DomainName=GetAtt(media_assets, 'DomainName'),
                CustomOriginConfig=cloudfront.CustomOrigin(
                    OriginProtocolPolicy='https-only'
                ),
            ),
        ],
        PriceClass='PriceClass_100',
    )
)

policy = iam.PolicyType(
    'AppPolicy',
    PolicyName='AppPolicy',
    Roles=[Ref(role)],
    PolicyDocument={
        'Statement': [
            {  # Lambda service
                'Action': ['lambda:InvokeFunction'],
                'Effect': 'Allow',
                'Resource': ['*']
            },
            {  # Media bucket
                'Action': "s3:*",
                'Effect': 'Allow',
                'Resource': [
                    GetAtt(media_assets, 'Arn'),
                    Sub('${arn}/*', **{'arn': GetAtt(media_assets, 'Arn')}),
                ]
            },
            {  # Static bucket
                'Action': "s3:*",
                'Effect': 'Allow',
                'Resource': [
                    GetAtt(static_assets, 'Arn'),
                    Sub('${arn}/*', **{'arn': GetAtt(static_assets, 'Arn')}),
                ]
            },
            {  # Source bucket
                "Action": "s3:GetObject",
                "Effect": "Allow",
                "Resource": Sub('${arn}/*', **{'arn': GetAtt(source, 'Arn')}),
            },
            {  # Secrets bucket
                "Action": "s3:GetObject",
                "Effect": "Allow",
                "Resource": Sub('${arn}/*', **{'arn': GetAtt(secrets, 'Arn')}),
            },
        ]
    }
)
