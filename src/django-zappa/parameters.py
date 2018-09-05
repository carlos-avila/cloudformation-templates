from troposphere import Parameter

slim_handler = Parameter(
    'ParametersSlimHandler',
    AllowedValues=['True', 'False'],
    Default='False',
    Description='Enable or disable the bucket used by Zappa slim_handler.',
    Type='String',
)
