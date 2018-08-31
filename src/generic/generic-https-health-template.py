#!/usr/bin/env python3

from troposphere import Ref, Join
from troposphere import Template, Parameter, route53, cloudwatch, sns

template = Template("""
Create a Route53 health check for a domain and notify of any alarms to the contacts provided.

Template: https-health-template.
Author: Carlos Avila <cavila@mandelbrew.com>.
""")

# region Parameters
email = template.add_parameter(Parameter(
    'Email',
    Default='alert@example.com',
    Description='Email address used for alarms',
    Type='String'
))

phone = template.add_parameter(Parameter(
    'Phone',
    Default='12223334444',
    Description='Phone number used for alarms',
    Type='String'
))

main_domain = template.add_parameter(Parameter(
    'MainDomain',
    AllowedPattern=('^(([a-zA-Z]{1})|([a-zA-Z]{1}[a-zA-Z]{1})|'
                    '([a-zA-Z]{1}[0-9]{1})|([0-9]{1}[a-zA-Z]{1})|'
                    '([a-zA-Z0-9][a-zA-Z0-9-_]{1,61}[a-zA-Z0-9]))\.'
                    '([a-zA-Z]{2,6}|[a-zA-Z0-9-]{2,30}\.[a-zA-Z]{2,3})$'),
    Default='example.com',
    Description='FQDN of the main domain or subdomain used to access the site.',
    MaxLength=100,
    MinLength=4,
    Type='String'
))
# endregion

# region Resources
notifications = template.add_resource(sns.Topic(
    'Notifications',
    Subscription=[
        sns.Subscription(
            Endpoint=Ref(email),
            Protocol='email'
        ),
        sns.Subscription(
            Endpoint=Ref(phone),
            Protocol='sms'
        )
    ]
))

main_domain_check = template.add_resource(route53.HealthCheck(
    'MainDomainCheck',
    HealthCheckConfig=route53.HealthCheckConfiguration(
        EnableSNI=True,
        FullyQualifiedDomainName=Ref(main_domain),
        Port='443',
        Type='HTTPS'
    )
))

main_domain_alarm = template.add_resource(cloudwatch.Alarm(
    'MainDomainAlarm',
    AlarmActions=[Ref(notifications)],
    AlarmDescription=Join('', ['Health check for ', Ref(main_domain)]),
    ComparisonOperator='LessThanThreshold',
    Dimensions=[
        cloudwatch.MetricDimension(Name='HealthCheckId', Value=Ref(main_domain_check))
    ],
    EvaluationPeriods=1,
    MetricName='HealthCheckStatus',
    Namespace='AWS/Route53',
    OKActions=[Ref(notifications)],
    Period=60,  # seconds
    Statistic='Minimum',
    Threshold='1.0',
))
# endregion

if __name__ == '__main__':
    print(template.to_json())
