from troposphere import Ref, Sub, GetAtt, s3, Join
from troposphere import codebuild, codepipeline, iam, sns

import parameters

from resources import app

# region Roles
build_role = iam.Role(
    'CiBuildRole',
    AssumeRolePolicyDocument={
        'Statement': [
            {
                'Action': 'sts:AssumeRole',
                'Effect': 'Allow',
                'Principal': {
                    'Service': 'codebuild.amazonaws.com'
                }
            }
        ]
    },
)

deploy_role = iam.Role(
    'CiDeployRole',
    AssumeRolePolicyDocument={
        'Statement': [
            {
                'Action': 'sts:AssumeRole',
                'Effect': 'Allow',
                'Principal': {
                    'Service': 'codebuild.amazonaws.com'
                }
            }
        ]
    },
)

pipeline_role = iam.Role(
    'CiPipelineRole',
    AssumeRolePolicyDocument={
        'Statement': [
            {
                'Action': 'sts:AssumeRole',
                'Effect': 'Allow',
                'Principal': {
                    'Service': 'codepipeline.amazonaws.com'
                }

            }
        ]
    },
)
# endregion

artifacts = s3.Bucket('CiArtifacts')

notifications = sns.Topic(
    'CiNotifications',
    Subscription=[
        sns.Subscription(Endpoint=Ref(parameters.email), Protocol='email')
    ]
)

build = codebuild.Project(
    'CiBuild',
    Name=Sub('${AWS::StackName}-CiBuild'),
    ServiceRole=Ref(build_role),
    Source=codebuild.Source(Type='CODEPIPELINE', BuildSpec='buildspec.yml'),
    Artifacts=codebuild.Artifacts(Type='CODEPIPELINE'),
    Environment=codebuild.Environment(
        Type='LINUX_CONTAINER',
        Image='aws/codebuild/docker:1.12.1',
        ComputeType='BUILD_GENERAL1_SMALL',
        EnvironmentVariables=[
            codebuild.EnvironmentVariable(
                Name='APP_DIST_DOMAIN',
                Type='PLAINTEXT',
                Value=GetAtt(app.distribution, 'DomainName'))
        ]
    )
)

deploy = codebuild.Project(
    'CiDeploy',
    Name=Sub('${AWS::StackName}-CiDeploy'),
    ServiceRole=Ref(deploy_role),
    Source=codebuild.Source(Type='CODEPIPELINE', BuildSpec='deployspec.yml'),
    Artifacts=codebuild.Artifacts(Type='CODEPIPELINE'),
    Environment=codebuild.Environment(
        Type='LINUX_CONTAINER',
        Image='aws/codebuild/docker:1.12.1',
        ComputeType='BUILD_GENERAL1_SMALL',
        EnvironmentVariables=[
            codebuild.EnvironmentVariable(
                Name='APP_STATIC',
                Type='PLAINTEXT',
                Value=Ref(app.static)),
        ]
    )
)

pipeline = codepipeline.Pipeline(
    'CiPipeline',
    RoleArn=GetAtt(pipeline_role, 'Arn'),
    ArtifactStore=codepipeline.ArtifactStore(
        Type='S3',
        Location=Ref(artifacts),
    ),
    Stages=[
        codepipeline.Stages(
            Name='Source',
            Actions=[
                codepipeline.Actions(
                    Name='Fetch',
                    RunOrder=1,
                    ActionTypeId=codepipeline.ActionTypeID(
                        Category='Source',
                        Owner='AWS',
                        Provider='S3',
                        Version='1',
                    ),
                    Configuration={
                        'S3Bucket': Ref(app.source),
                        'S3ObjectKey': 'source.zip',
                    },
                    OutputArtifacts=[
                        codepipeline.OutputArtifacts(Name=app.source.title)
                    ],
                )
            ]
        ),
        codepipeline.Stages(
            Name='Build',
            Actions=[
                codepipeline.Actions(
                    Name='Source',
                    RunOrder=1,
                    ActionTypeId=codepipeline.ActionTypeID(
                        Category='Build',
                        Owner='AWS',
                        Provider='CodeBuild',
                        Version='1',
                    ),
                    Configuration={
                        'ProjectName': Ref(build),
                    },
                    InputArtifacts=[
                        codepipeline.InputArtifacts(Name=app.source.title)
                    ],
                    OutputArtifacts=[
                        codepipeline.OutputArtifacts(Name=build.title)
                    ],
                )
            ]
        ),
        codepipeline.Stages(
            Name='Production',
            Actions=[
                codepipeline.Actions(
                    Name='Approve',
                    RunOrder=1,
                    ActionTypeId=codepipeline.ActionTypeID(
                        Category='Approval',
                        Owner='AWS',
                        Provider='Manual',
                        Version='1',
                    ),
                    Configuration={
                        'NotificationArn': Ref(notifications),
                        'CustomData': Sub('A new change is waiting for ${AWS::StackName}')
                    }
                ),
                codepipeline.Actions(
                    Name='Deploy',
                    RunOrder=2,
                    ActionTypeId=codepipeline.ActionTypeID(
                        Category='Test',
                        Owner='AWS',
                        Provider='CodeBuild',
                        Version='1',
                    ),
                    Configuration={
                        'ProjectName': Ref(deploy),
                    },
                    InputArtifacts=[
                        codepipeline.InputArtifacts(Name=build.title)
                    ],
                ),
            ]
        ),
    ]
)

# region Policies
build_policy = iam.PolicyType(
    'CiBuildPolicy',
    PolicyName='CiBuildPolicy',
    Roles=[Ref(build_role)],
    PolicyDocument={
        'Statement': [
            # Logs (required)
            {
                'Action': [
                    'logs:CreateLogGroup',
                    'logs:CreateLogStream',
                    'logs:PutLogEvents'
                ],
                'Effect': 'Allow',
                'Resource': '*'
            },
            # Decryption keys (required)
            {
                'Action': [
                    'kms:GenerateDataKey*',
                    'kms:Encrypt',
                    'kms:Decrypt',
                ],
                'Effect': 'Allow',
                'Resource': [
                    Sub('arn:aws:kms:${AWS::Region}:${AWS::AccountId}:/alias/aws/s3'),
                ]
            },
            # artifacts
            {
                'Action': [
                    's3:PutObject',
                    's3:GetObject',
                    's3:GetObjectVersion'
                ],
                'Effect': 'Allow',
                'Resource': [
                    Join('', [GetAtt(artifacts, 'Arn'), '']),
                    Join('', [GetAtt(artifacts, 'Arn'), '/*']),
                ]
            }
        ],
    },
)

deploy_policy = iam.PolicyType(
    'CiDeployPolicy',
    PolicyName='CiDeployPolicy',
    Roles=[Ref(deploy_role)],
    PolicyDocument={
        'Statement': [
            # Logs (required)
            {
                'Action': [
                    'logs:CreateLogGroup',
                    'logs:CreateLogStream',
                    'logs:PutLogEvents'
                ],
                'Effect': 'Allow',
                'Resource': '*'
            },
            # Decryption keys (required)
            {
                'Action': [
                    'kms:GenerateDataKey*',
                    'kms:Encrypt',
                    'kms:Decrypt',
                ],
                'Effect': 'Allow',
                'Resource': [
                    Sub('arn:aws:kms:${AWS::Region}:${AWS::AccountId}:/alias/aws/s3'),
                ]
            },
            # artifacts and static
            {
                'Action': [
                    's3:PutObject',
                    's3:GetObject',
                    's3:GetObjectVersion'
                ],
                'Effect': 'Allow',
                'Resource': [
                    Join('', [GetAtt(artifacts, 'Arn'), '']),
                    Join('', [GetAtt(artifacts, 'Arn'), '/*']),
                    Join('', [GetAtt(app.static, 'Arn'), '']),
                    Join('', [GetAtt(app.static, 'Arn'), '/*']),
                ]
            }
        ],
    },
)

pipeline_policy = iam.PolicyType(
    'CiPipelinePolicy',
    PolicyName='CiPipelinePolicy',
    Roles=[Ref(pipeline_role)],
    PolicyDocument={
        'Statement': [
            # Source
            {
                'Action': [
                    's3:GetObject',
                    's3:GetObjectVersion',
                    's3:GetBucketVersioning',
                ],
                'Effect': 'Allow',
                'Resource': [
                    Join('', [GetAtt(app.source, 'Arn'), '']),
                    Join('', [GetAtt(app.source, 'Arn'), '/*']),
                ]
            },
            # Artifacts
            {
                'Action': [
                    's3:GetObject',
                    's3:GetObjectVersion',
                    's3:GetBucketVersioning',
                    's3:PutObject'
                ],
                'Effect': 'Allow',
                'Resource': [
                    Join('', [GetAtt(artifacts, 'Arn'), '']),
                    Join('', [GetAtt(artifacts, 'Arn'), '/*'])
                ]
            },
            # CodeBuild
            {
                'Action': [
                    'codebuild:StartBuild',
                    'codebuild:BatchGetBuilds',
                    'codebuild:StopBuild'
                ],
                'Effect': 'Allow',
                'Resource': [
                    GetAtt(build, 'Arn'),
                    GetAtt(deploy, 'Arn'),
                ]
            },
            # SNS
            {
                'Action': [
                    'sns:Publish',
                ],
                'Effect': 'Allow',
                'Resource': [
                    Ref(notifications),
                ]
            }
        ]
    }
)

# endregion
