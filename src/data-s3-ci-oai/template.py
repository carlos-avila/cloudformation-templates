#!/usr/bin/env python3

from troposphere import Template

import parameters
import outputs
from resources import app, ci

template = Template("""
Template for serving static content.

Provides a S3 source, CD/CI pipeline, hosted in S3, and served by CloudFront with CORS configured.

Template: data-s3-ci-oai.
Author: Carlos Avila <cavila@mandelbrew.com>.
""")

# region Parameters
template.add_parameter(parameters.email)
# endregion

# region App
template.add_resource(app.source)
template.add_resource(app.static)
template.add_resource(app.oai)
template.add_resource(app.distribution)
template.add_resource(app.static_policy)
# endregion

# region CI
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
# endregion

# region Metadata
template.add_metadata({
    'AWS::CloudFormation::Interface': {
        'ParameterLabels': {
            # CI
            parameters.email.title: {'default': 'Notifications'},
        },
        'ParameterGroups': [
            {
                'Label': {'default': 'CI/CD'},
                'Parameters': [
                    parameters.email.title,
                ]
            }
        ]
    }
})
# endregion

if __name__ == '__main__':
    print(template.to_json())
