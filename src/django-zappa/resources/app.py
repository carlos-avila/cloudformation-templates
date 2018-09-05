from troposphere import If
from troposphere import Ref, Sub, GetAtt
from troposphere import s3, iam

import conditions

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
    Condition=conditions.has_slim_handler
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

policy = iam.PolicyType(
    'AppPolicy',
    PolicyName='AppPolicy',
    Roles=[Ref(role)],
    PolicyDocument={
        'Statement': [
            {  # CloudWatch
                "Effect": "Allow",
                "Action": [
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:DescribeLogStreams",
                    "logs:PutLogEvents",
                ],
                "Resource": "arn:aws:logs:*",
            },
            {  # Lambda
                'Action': ['lambda:InvokeFunction'],
                'Effect': 'Allow',
                'Resource': 'arn:aws:lambda:*'
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
            {  # Secrets bucket
                "Action": "s3:GetObject",
                "Effect": "Allow",
                "Resource": Sub('${arn}/*', **{'arn': GetAtt(secrets, 'Arn')}),
            },
            If(  # Source bucket
                conditions.has_slim_handler,
                {
                    "Action": "s3:GetObject",
                    "Effect": "Allow",
                    "Resource": Sub('${arn}/*', **{'arn': GetAtt(source, 'Arn')}),
                },
                Ref('AWS::NoValue')
            )
        ]
    }
)
