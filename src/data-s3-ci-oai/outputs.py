from troposphere import GetAtt
from troposphere import Output

from resources import app

distribution_domain = Output(
    'OutputsAppDistributionDomainName',
    Value=GetAtt(app.distribution, 'DomainName')
)