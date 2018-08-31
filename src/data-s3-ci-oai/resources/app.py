from troposphere import Ref, GetAtt, Join
from troposphere import s3, cloudfront

source = s3.Bucket(
    'AppSource',
    VersioningConfiguration=s3.VersioningConfiguration(Status='Enabled')
)

static = s3.Bucket(
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
)

oai = cloudfront.CloudFrontOriginAccessIdentity(
    'AppDistributionOai',
    CloudFrontOriginAccessIdentityConfig=cloudfront.CloudFrontOriginAccessIdentityConfig(
        Comment=Ref(static)
    )
)

distribution = cloudfront.Distribution(
    'AppDistribution',
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
)

# region Policies
static_policy = s3.BucketPolicy(
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
                    Join('', [GetAtt(static, 'Arn'), '/*']),
                ]
            }
        ]
    }
)
# endregion
