from troposphere import GetAtt
from troposphere import Output

from resources import app

distribution_domain = Output(
    'OutputsAppDistributionDomainName',
    Condition='CreateDistribution',
    Value=GetAtt(app.distribution, 'DomainName')
)

website_url = Output(
    'OutputsAppBuildWebsiteURL',
    Value=GetAtt(app.build, 'WebsiteURL')
)
