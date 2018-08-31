from troposphere import Parameter

email = Parameter(
    'ParametersEmail',
    Description='Email address used for notifications',
    Type='String'
)

source_provider = Parameter(
    'ParametersSourceProvider',
    AllowedValues=['S3', 'CodeCommit'],
    Default='S3',
    Description='Input source for the CD/CI pipeline.',
    Type='String'
)
