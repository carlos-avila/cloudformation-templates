from troposphere import Sub, Ref, GetAtt
from troposphere import codecommit, s3

from resources.dev import app as dev_app
from resources.test import app as test_app
from resources.prod import app as prod_app

secrets = s3.Bucket(
    'AppSecrets',
    VersioningConfiguration=s3.VersioningConfiguration(Status='Enabled'),
)

source = s3.Bucket(
    'AppSource',
)

source_policy = s3.BucketPolicy(
    'AppSourcePolicy',
    Bucket=Ref(source),
    PolicyDocument={
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "AWS": GetAtt(dev_app.role, 'Arn'),
                },
                "Action": "s3:GetObject",
                "Resource": Sub('${{{0}.Arn}}/dev_*'.format(source.title))
            },
            {
                "Effect": "Allow",
                "Principal": {
                    "AWS": GetAtt(test_app.role, 'Arn'),
                },
                "Action": "s3:GetObject",
                "Resource": Sub('${{{0}.Arn}}/test_*'.format(source.title))
            },
            {
                "Effect": "Allow",
                "Principal": {
                    "AWS": GetAtt(prod_app.role, 'Arn'),
                },
                "Action": "s3:GetObject",
                "Resource": Sub('${{{0}.Arn}}/prod_*'.format(source.title))
            }
        ]
    }
)

secrets_policy = s3.BucketPolicy(
    'AppSecretsPolicy',
    Bucket=Ref(secrets),
    PolicyDocument={
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "AWS": GetAtt(dev_app.role, 'Arn'),
                },
                "Action": "s3:GetObject",
                "Resource": Sub('${{{0}.Arn}}/dev-env.json'.format(secrets.title))
            },
            {
                "Effect": "Allow",
                "Principal": {
                    "AWS": GetAtt(test_app.role, 'Arn'),
                },
                "Action": "s3:GetObject",
                "Resource": Sub('${{{0}.Arn}}/test-env.json'.format(secrets.title))
            },
            {
                "Effect": "Allow",
                "Principal": {
                    "AWS": GetAtt(prod_app.role, 'Arn'),
                },
                "Action": "s3:GetObject",
                "Resource": Sub('${{{0}.Arn}}/prod-env.json'.format(secrets.title))
            }
        ]
    }
)
