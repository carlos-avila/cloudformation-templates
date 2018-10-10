from troposphere import GetAtt
from troposphere import Output

from resources import app

website_url = Output(
    'OutputsAppBuildWebsiteURL',
    Value=GetAtt(app.build, 'WebsiteURL')
)
