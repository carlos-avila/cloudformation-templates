from troposphere import Parameter

allowed_methods = Parameter(
    'ParametersAllowedMethods',
    Default='GET',
    Description='HTTP methods that you allow the origin to execute.',
    Type='CommaDelimitedList'
)

allowed_origins = Parameter(
    'ParametersAllowedOrigins',
    Default='*',
    Description='An origin that you allow to send cross-domain requests (CORS).',
    Type='CommaDelimitedList'
)

email = Parameter(
    'ParametersEmail',
    Description='Email address used for notifications',
    Type='String'
)

exposed_headers = Parameter(
    'ParametersExposedHeaders',
    Default='',
    Description='One or more headers in the response that are accessible to client applications.',
    Type='CommaDelimitedList'
)

require_approval = Parameter(
    'ParametersRequireApproval',
    AllowedValues=['True', 'False'],
    Default='False',
    Description='Require review step before deploying.',
    Type='String',
)

source_provider = Parameter(
    'ParametersSourceProvider',
    AllowedValues=['S3', 'CodeCommit'],
    Default='S3',
    Description='Input source for the CD/CI pipeline.',
    Type='String'
)
