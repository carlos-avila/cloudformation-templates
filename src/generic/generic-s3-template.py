#!/usr/bin/env python3

from troposphere import GetAtt, Ref
from troposphere import Equals, If, And, Condition
from troposphere import Template, Parameter, Output
from troposphere import s3

template = Template("""Create and configure S3 bucket resource.

Creates the following resources:
    - S3 bucket: can be used to server files with CORS or as a static website with version control.

Template: generic-s3.
Author: Carlos Avila <cavila@mandelbrew.com>
""")

# region Parameters
website = template.add_parameter(Parameter(
    'Website',
    AllowedValues=['True', 'False'],
    Default='False',
    Description='Enable or disable the bucket as a static website.',
    Type='String',
))
cors = template.add_parameter(Parameter(
    'Cors',
    AllowedValues=['True', 'False'],
    Default='False',
    Description='Enable or disable cross-origin resource sharing of objects in this bucket.',
    Type='String',
))
versioning = template.add_parameter(Parameter(
    'Versioning',
    AllowedValues=['True', 'False'],
    Default='False',
    Description='Enable or disable keeping multiple variants of all objects in this bucket.',
    Type='String',
))
history_limit = template.add_parameter(Parameter(
    'HistoryLimit',
    AllowedValues=['True', 'False'],
    Default='False',
    Description='Enable or disable a limit to the multiple variants of all objects in this bucket.',
    Type='String',
))
history_limit_days = template.add_parameter(Parameter(
    'HistoryLimitDays',
    Default='0',
    Description='Amount in days to keep old versions of all objects in this bucket.',
    Type='Number',
))
# endregion

# region Conditions
has_website = template.add_condition(
    'HasWebsite',
    Equals(Ref(website), 'True')
)
has_cors = template.add_condition(
    'HasCors',
    Equals(Ref(cors), 'True')
)
has_versioning = template.add_condition(
    'HasVersioning',
    Equals(Ref(versioning), 'True')
)
has_history_limit = template.add_condition(
    'HasHistoryLimit',
    And(
        Condition(has_versioning),
        Equals(Ref(history_limit), 'True')
    ),
)
# endregion

# region Resources
# endregion
bucket = template.add_resource(s3.Bucket(
    'Bucket',
    CorsConfiguration=If(
        has_cors,
        s3.CorsConfiguration(
            CorsRules=[
                s3.CorsRules(
                    AllowedHeaders=['Authorization'],
                    AllowedMethods=['GET'],
                    AllowedOrigins=['*'],
                    ExposedHeaders=[],
                    MaxAge=3600,
                )
            ]
        ),
        Ref('AWS::NoValue')
    ),
    LifecycleConfiguration=If(
        has_history_limit,
        s3.LifecycleConfiguration(
            Rules=[
                s3.LifecycleRule(
                    AbortIncompleteMultipartUpload=s3.AbortIncompleteMultipartUpload(DaysAfterInitiation=3),
                    Id='History Limit',
                    NoncurrentVersionExpirationInDays=Ref(history_limit_days),
                    Status='Enabled',
                )
            ]
        ),
        Ref('AWS::NoValue')
    ),
    WebsiteConfiguration=If(
        has_website,
        s3.WebsiteConfiguration(IndexDocument='index.html', ErrorDocument='404.html'),
        Ref('AWS::NoValue')
    )
    ,
    VersioningConfiguration=If(
        has_versioning,
        s3.VersioningConfiguration(Status='Enabled'),
        Ref('AWS::NoValue')
    ),
))

# region Outputs
template.add_output(
    Output('ARN', Value=GetAtt(bucket, 'Arn'))
)
template.add_output(
    Output('DomainName', Value=GetAtt(bucket, 'DomainName'))
)
template.add_output(
    Output('WebsiteURL', Value=GetAtt(bucket, 'WebsiteURL'))
)
# endregion

# region Metadata
template.add_metadata({
    'AWS::CloudFormation::Interface': {
        'ParameterLabels': {
            website.title: {'default': 'Enable Static Website?'},
            cors.title: {'default': 'Enable CORS?'},
            versioning.title: {'default': 'Enable Versioning?'},
            history_limit.title: {'default': 'Enable History Limit?'},
            history_limit_days.title: {'default': 'History Limit'},
        },
        'ParameterGroups': [
            {
                'Label': {'default': 'Static Website'},
                'Parameters': [
                    website.title,
                    cors.title,
                ]
            },
            {
                'Label': {'default': 'Versioning'},
                'Parameters': [
                    versioning.title,
                    history_limit.title,
                    history_limit_days.title,
                ]
            },
        ]
    }
})
# endregion

if __name__ == '__main__':
    print(template.to_json())
