from troposphere import Output, GetAtt, Ref

from resources import app

app_source = Output(
    'AppSource',
    Value=Ref(app.source),
)

app_secrets = Output(
    'AppSecrets',
    Value=Ref(app.secrets)
)

app_media = Output(
    'AppMedia',
    Value=Ref(app.media_assets)
)
app_static = Output(
    'AppStatic',
    Value=Ref(app.static_assets)
)
app_distribution = Output(
    'AppDistribution',
    Value=GetAtt(app.distribution, 'DomainName')
)
app_role_arn = Output(
    'AppRoleArn',
    Value=GetAtt(app.role, 'Arn')
)
app_role_name = Output(
    'AppRoleName',
    Value=Ref(app.role)
)
