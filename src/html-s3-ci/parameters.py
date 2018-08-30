from troposphere import Parameter

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

dist_aliases = Parameter(
    'DistributionAliases',
    AllowedPattern='^((\d+)(,\s*\d+)*)*$',
    ConstraintDescription='must be comma-delimited FQDNs.',
    Description='CNAMEs (alternate domain names), if any, for the distribution.',
    Type='String'
)
