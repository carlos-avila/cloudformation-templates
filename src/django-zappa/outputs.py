from troposphere import Output, GetAtt, Ref

from resources import app

import conditions

app_source = Output(
    'AppSource',
    Condition=conditions.has_slim_handler,
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
app_role_arn = Output(
    'AppRoleArn',
    Value=GetAtt(app.role, 'Arn')
)
app_role_name = Output(
    'AppRoleName',
    Value=Ref(app.role)
)
