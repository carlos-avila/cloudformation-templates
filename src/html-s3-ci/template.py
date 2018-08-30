#!/usr/bin/env python3

from troposphere import Ref, Equals, Condition, Not
from troposphere import Template

from resources import app, ci

import parameters
import outputs

template = Template("""Provides resources for serving web static content with continuous deployment.

Creates the following resources:
    - S3 bucket: source code.
    - S3 bucket: built code.
    - CloudFront distribution:

In addition, the following resources are created for CD/CI:
    - S3 bucket: artifacts used by the pipeline.
    - SNS topic: pipeline notifications.
    - CodeBuild project: build.
    - CodeBuild project: deploy.
    - CodeBuild pipeline: Flow control for fetch, build and deploy.
      

Template: html-s3-ci.
Author: Carlos Avila <cavila@mandelbrew.com>.
""")

# region Parameters
template.add_parameter(parameters.email)
template.add_parameter(parameters.create_dist)
template.add_parameter(parameters.dist_aliases)
# endregion

# region Conditions
# template.add_condition('UseSourceS3', Equals('', 'S3'))
# template.add_condition('NotUseSourceS3', Not(Condition('UseSourceS3')))
template.add_condition('CreateDistribution', Equals(Ref(parameters.create_dist), 'true'))
template.add_condition('UseDistributionAliases', Not(Equals(Ref(parameters.dist_aliases), '')))
# endregion

# region Resources
# App
template.add_resource(app.source)
template.add_resource(app.build)
template.add_resource(app.distribution)
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
template.add_output(outputs.distribution_domain)
template.add_output(outputs.website_url)
# endregion

# region Metadata
template.add_metadata({
    'AWS::CloudFormation::Interface': {
        'ParameterLabels': {
            parameters.email.title: {'default': 'Notifications'},
            # CDN
            parameters.create_dist.title: {'default': 'Create CDN'},
            parameters.dist_aliases.title: {'default': 'CDN Aliases'},
        },
        'ParameterGroups': [
            {
                'Label': {'default': 'General'},
                'Parameters': [
                    parameters.email.title,
                ]
            },
            {
                'Label': {'default': 'CDN'},
                'Parameters': [
                    parameters.create_dist.title,
                    parameters.dist_aliases.title,
                ]
            },
        ]
    }
})
# endregion

if __name__ == '__main__':
    print(template.to_json())
