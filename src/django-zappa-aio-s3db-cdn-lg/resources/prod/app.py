from troposphere import Ref, Sub, GetAtt
from troposphere import s3, iam, cloudfront

role = iam.Role(
    'AppProdRole',
    AssumeRolePolicyDocument={
        'Statement': [
            {
                'Action': 'sts:AssumeRole',
                'Effect': 'Allow',
                'Principal': {
                    'Service': [
                        'events.amazonaws.com',
                        'apigateway.amazonaws.com',
                        'lambda.amazonaws.com'
                    ]
                }
            }
        ]
    }
)

static_assets = s3.Bucket(
    'AppProdStaticAssets',
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
    'AppProdStaticAssetsPolicy',
    Bucket=Ref(static_assets),
    PolicyDocument={
        'Statement': [
            {
                'Action': ['s3:GetObject'],
                'Effect': 'Allow',
                'Principal': '*',
                'Resource': [
                    Sub('${{{0}.Arn}}/*'.format(static_assets.title))
                ]
            }
        ]
    }
)

media_assets = s3.Bucket(
    'AppProdMediaAssets',
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
    'AppProdMediaAssetsPolicy',
    Bucket=Ref(media_assets),
    PolicyDocument={
        'Statement': [
            {
                'Action': ['s3:GetObject'],
                'Effect': 'Allow',
                'Principal': '*',
                'Resource': [
                    Sub('${{{0}.Arn}}/*'.format(media_assets.title))
                ]
            }
        ]
    }
)

database = s3.Bucket(
    'AppProdDatabase',
    VersioningConfiguration=s3.VersioningConfiguration(
        Status='Enabled'
    ),
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

database_policy = s3.BucketPolicy(
    'AppProdDatabasePolicy',
    Bucket=Ref(database),
    PolicyDocument={
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "AWS": GetAtt(role, 'Arn'),
                },
                "Action": "s3:GetObject",
                "Resource": Sub('${{{0}.Arn}}/*'.format(database.title))
            },
        ]
    }
)

distribution = cloudfront.Distribution(
    'AppProdDistribution',
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
        Comment=Sub('${AWS::StackName}-prod'),
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
    'AppProdPolicy',
    PolicyName='AppProdPolicy',
    Roles=[Ref(role)],
    PolicyDocument={
        'Statement': [
            {
                'Effect': 'Allow',
                'Action': [
                    'logs:*'
                ],
                'Resource': 'arn:aws:logs:*:*:*'
            },
            {
                'Effect': 'Allow',
                'Action': [
                    'lambda:InvokeFunction'
                ],
                'Resource': [
                    '*'
                ]
            },
            {
                'Effect': 'Allow',
                'Action': [
                    's3:ListBucket'
                ],
                'Resource': 'arn:aws:s3:::*'
            }
        ]
    }
)
