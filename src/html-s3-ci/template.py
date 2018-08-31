#!/usr/bin/env python3

from troposphere import Ref, Equals, Condition, Not
from troposphere import Template

from resources import app, ci

import parameters
import outputs

template = Template("""Provides resources for serving static web content with continuous deployment.

Creates the following resources:
    - S3 bucket (optional): source code.
    - CodeCommit repository (optional): source code.
    - S3 bucket: built code.

In addition, the following resources are created for CD/CI:
    - SNS topic: pipeline notifications.
    - S3 bucket: artifacts used by the pipeline.
    - CodeBuild project: build.
    - CodeBuild project: deploy.
    - CodeBuild pipeline: Flow control for fetch, build and deploy.

It works well with:
    - html-cdn-dns      

Template: html-s3-ci.
Author: Carlos Avila <cavila@mandelbrew.com>.
""")

# region Parameters
template.add_parameter(parameters.email)
template.add_parameter(parameters.source_provider)
# endregion

# region Conditions
template.add_condition(
    'UseSourceS3',
    Equals(Ref(parameters.source_provider), 'S3')
)
template.add_condition(
    'UseSourceRepo',
    Not(Condition('UseSourceS3'))
)
# endregion

# region Resources
# App
template.add_resource(app.source_bucket)
template.add_resource(app.source_repo)
template.add_resource(app.build)
template.add_resource(app.build_policy)
# endregion

# CD/CI
template.add_resource(ci.build_role)
template.add_resource(ci.deploy_role)
template.add_resource(ci.pipeline_role)

template.add_resource(ci.artifacts)
template.add_resource(ci.notifications)
template.add_resource(ci.build)
template.add_resource(ci.deploy)
template.add_resource(ci.pipeline)

template.add_resource(ci.build_policy)
template.add_resource(ci.deploy_policy)
template.add_resource(ci.pipeline_policy)
# endregion

# region Outputs
template.add_output(outputs.website_url)
# endregion

# region Metadata
template.add_metadata({
    'AWS::CloudFormation::Interface': {
        'ParameterLabels': {
            parameters.source_provider.title: {'default': 'Source Provider'},
            parameters.email.title: {'default': 'Notifications'},
        },
        'ParameterGroups': [
            {
                'Label': {'default': 'Pipeline'},
                'Parameters': [
                    parameters.email.title,
                    parameters.source_provider.title,
                ]
            },
        ]
    }
})
# endregion

if __name__ == '__main__':
    print(template.to_json())
