from troposphere import Ref, GetAtt, Sub
from troposphere import s3, codecommit

source_bucket = s3.Bucket(
    'AppSource',
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
    Condition='UseSourceRepo',
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
