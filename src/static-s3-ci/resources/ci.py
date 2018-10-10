from troposphere import Ref, Sub, GetAtt, If
from troposphere import codebuild, codepipeline, iam, sns, s3, events

import parameters
import conditions

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
        Image='aws/codebuild/docker:17.09.0',
        ComputeType='BUILD_GENERAL1_SMALL',
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
        Image='aws/codebuild/docker:17.09.0',
        ComputeType='BUILD_GENERAL1_SMALL',
        EnvironmentVariables=[
            codebuild.EnvironmentVariable(
                Name='APP_BUILD',
                Type='PLAINTEXT',
                Value=Ref(app.build)),
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
                    ActionTypeId=codepipeline.ActionTypeId(
                        Category='Source',
                        Owner='AWS',
                        Provider=Ref(parameters.source_provider),
                        Version='1',
                    ),
                    Configuration=If(
                        'UseSourceS3',
                        {
                            'S3Bucket': Ref(app.source_bucket),
                            'S3ObjectKey': 'source.zip',
                        },
                        {
                            'BranchName': 'master',
                            'RepositoryName': GetAtt(app.source_repo, 'Name'),
                        },
                    ),
                    OutputArtifacts=[
                        codepipeline.OutputArtifacts(
                            Name=If('UseSourceS3', app.source_bucket.title, app.source_repo.title)
                        )
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
                    ActionTypeId=codepipeline.ActionTypeId(
                        Category='Build',
                        Owner='AWS',
                        Provider='CodeBuild',
                        Version='1',
                    ),
                    Configuration={
                        'ProjectName': Ref(build),
                    },
                    InputArtifacts=[
                        codepipeline.InputArtifacts(
                            Name=If('UseSourceS3', app.source_bucket.title, app.source_repo.title)
                        )
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
                If(
                    conditions.RequireApproval,
                    codepipeline.Actions(
                        Name='Approve',
                        RunOrder=1,
                        ActionTypeId=codepipeline.ActionTypeId(
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
                    Ref('AWS::NoValue')
                ),
                codepipeline.Actions(
                    Name='Deploy',
                    RunOrder=2,
                    ActionTypeId=codepipeline.ActionTypeId(
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

pipeline_events = events.Rule(
    'CiPipelineEvents',
    Description='Notify of changes in pipeline',
    EventPattern={
        'source': ['aws.codepipeline'],
        'detail-type': ['CodePipeline Pipeline Execution State Change'],
        'detail': {
            'state': ['SUCCEEDED', 'FAILED'],
            'pipeline': [Ref(pipeline)]
        }
    },
    Targets=[
        events.Target(
            Arn=Ref(notifications),
            Id='PipelineChange',
            InputTransformer=events.InputTransformer(
                InputPathsMap={
                    'pipeline': '$.detail.pipeline',
                    'state': '$.detail.state'
                },
                InputTemplate='"Pipeline <pipeline> has <state>."'

            )
        )
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
                    Sub('${arn}', **{'arn': GetAtt(artifacts, 'Arn')}),
                    Sub('${arn}/*', **{'arn': GetAtt(artifacts, 'Arn')}),
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
                    Sub('${arn}', **{'arn': GetAtt(artifacts, 'Arn')}),
                    Sub('${arn}/*', **{'arn': GetAtt(artifacts, 'Arn')}),
                    Sub('${arn}', **{'arn': GetAtt(app.build, 'Arn')}),
                    Sub('${arn}/*', **{'arn': GetAtt(app.build, 'Arn')}),
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
            If(
                'UseSourceS3',
                {  # S3 bucket
                    'Action': [
                        's3:GetObject',
                        's3:GetObjectVersion',
                        's3:GetBucketVersioning',
                    ],
                    'Effect': 'Allow',
                    'Resource': [
                        Sub('${arn}', **{'arn': GetAtt(app.source_bucket, 'Arn')}),
                        Sub('${arn}/*', **{'arn': GetAtt(app.source_bucket, 'Arn')}),
                    ]
                },
                {  # CodeCommit repo
                    "Action": [
                        'codecommit:CancelUploadArchive',
                        'codecommit:GetBranch',
                        'codecommit:GetCommit',
                        'codecommit:GetUploadArchiveStatus',
                        'codecommit:UploadArchive',
                    ],
                    "Effect": "Allow",
                    "Resource": [
                        GetAtt(app.source_repo, 'Arn'),
                    ]
                }
            ),
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
                    Sub('${arn}', **{'arn': GetAtt(artifacts, 'Arn')}),
                    Sub('${arn}/*', **{'arn': GetAtt(artifacts, 'Arn')}),
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
