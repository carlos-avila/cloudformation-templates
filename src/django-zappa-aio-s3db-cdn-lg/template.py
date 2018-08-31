#!/usr/bin/env python3

from troposphere import Template

from resources import app
from resources.dev import app as dev_app
from resources.test import app as test_app
from resources.prod import app as prod_app

import outputs

template = Template("""Provides all resources needed for a simple serverless Django application with three environments (all-in-one).

Creates the following resources:
    - S3 bucket: Zappa slim_handler bucket.
    - S3 bucket: secret environment variables. 

In addition, the following resources are created for each environment:
    - S3 bucket: database (check zappa-django-utils: s3sqlite).
    - S3 bucket: static assets.
    - S3 bucket: media assets.
    - CloudFront distribution: configured to handle static and media assets.

Template: zappa-s3db-cdn-lg.
Author: Carlos Avila <cavila@mandelbrew.com>.
""")

# region App
template.add_resource(app.source)
template.add_resource(app.source_policy)
template.add_resource(app.secrets)
template.add_resource(app.secrets_policy)
# dev
template.add_resource(dev_app.role)
template.add_resource(dev_app.static_assets)
template.add_resource(dev_app.static_assets_policy)
template.add_resource(dev_app.media_assets)
template.add_resource(dev_app.media_assets_policy)
template.add_resource(dev_app.database)
template.add_resource(dev_app.database_policy)
template.add_resource(dev_app.distribution)
template.add_resource(dev_app.policy)
# test
template.add_resource(test_app.role)
template.add_resource(test_app.static_assets)
template.add_resource(test_app.static_assets_policy)
template.add_resource(test_app.media_assets)
template.add_resource(test_app.media_assets_policy)
template.add_resource(test_app.database)
template.add_resource(test_app.database_policy)
template.add_resource(test_app.distribution)
template.add_resource(test_app.policy)
# prod
template.add_resource(prod_app.role)
template.add_resource(prod_app.static_assets)
template.add_resource(prod_app.static_assets_policy)
template.add_resource(prod_app.media_assets)
template.add_resource(prod_app.media_assets_policy)
template.add_resource(prod_app.database)
template.add_resource(prod_app.database_policy)
template.add_resource(prod_app.distribution)
template.add_resource(prod_app.policy)
# endregion

# region Outputs
template.add_output(outputs.app_source)
template.add_output(outputs.app_secrets)
# Dev
template.add_output(outputs.app_dev_media)
template.add_output(outputs.app_dev_static)
template.add_output(outputs.app_dev_database)
template.add_output(outputs.app_dev_distribution)
template.add_output(outputs.app_dev_role_arn)
template.add_output(outputs.app_dev_role_name)
# Test
template.add_output(outputs.app_test_media)
template.add_output(outputs.app_test_static)
template.add_output(outputs.app_test_database)
template.add_output(outputs.app_test_role_arn)
template.add_output(outputs.app_test_role_name)
# Prod
template.add_output(outputs.app_prod_media)
template.add_output(outputs.app_prod_static)
template.add_output(outputs.app_prod_database)
template.add_output(outputs.app_prod_role_arn)
template.add_output(outputs.app_prod_role_name)
# endregion

if __name__ == '__main__':
    print(template.to_json())
