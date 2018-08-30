from troposphere import Parameter

source_provider = Parameter(
    'ParametersSourceProvider',
    AllowedValues=['S3', 'CodeCommit'],
    Default='S3',
    Description='Input source for the CD/CI pipeline.',
    Type='String'
)

email = Parameter(
    'ParametersEmail',
    Description='Email address used for notifications',
    Type='String'
)

create_dist = Parameter(
    'ParametersCreateDistribution',
    AllowedValues=['true', 'false'],
    Default='true',
    Description='Setup CloudFront as a CDN.',
    Type='String'
)

aliases = Parameter(
    'ParametersAliases',
    AllowedPattern='^((\d+)(,\s*\d+)*)*$',
    ConstraintDescription='must be comma-delimited FQDNs.',
    Description='CNAMEs (alternate domain names), if any, for the distribution.',
    Type='String'
)
