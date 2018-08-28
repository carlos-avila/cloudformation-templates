#!/usr/bin/env python3

from troposphere import Template

from resources import app

import outputs

template = Template("""Provides basic resources needed for a serverless Django application.

Creates the following resources:
    - S3 bucket: Zappa slim_handler bucket.
    - S3 bucket: secret environment variables. 

In addition, the following resources are created for each environment:
    - S3 bucket: static assets.
    - S3 bucket: media assets.
    - CloudFront distribution: configured to handle static and media assets.

Template: zappa-cdn-lg.
Author: Carlos Avila <cavila@mandelbrew.com>.
""")

# region App
template.add_resource(app.role)
template.add_resource(app.secrets)
template.add_resource(app.source)
template.add_resource(app.static_assets)
template.add_resource(app.static_assets_policy)
template.add_resource(app.media_assets)
template.add_resource(app.media_assets_policy)
template.add_resource(app.distribution)
template.add_resource(app.policy)
# endregion

# region Outputs
template.add_output(outputs.app_source)
template.add_output(outputs.app_secrets)
template.add_output(outputs.app_media)
template.add_output(outputs.app_static)
template.add_output(outputs.app_distribution)
template.add_output(outputs.app_role_arn)
template.add_output(outputs.app_role_name)
# endregion

if __name__ == '__main__':
    print(template.to_json())
