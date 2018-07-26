from troposphere import Output, GetAtt, Ref

from resources import app
from resources.dev import app as dev_app
from resources.test import app as test_app
from resources.prod import app as prod_app

app_source = Output(
    'AppSource',
    Value=Ref(app.source),
)

app_secrets = Output(
    'AppSecrets',
    Value=Ref(app.secrets)
)

# region Dev
app_dev_media = Output(
    'AppDevMedia',
    Value=Ref(dev_app.media_assets)
)
app_dev_static = Output(
    'AppDevStatic',
    Value=Ref(dev_app.static_assets)
)
app_dev_distribution = Output(
    'AppDevDistribution',
    Value=Ref(dev_app.distribution)
)
app_dev_role_arn = Output(
    'AppDevRoleArn',
    Value=GetAtt(dev_app.role, 'Arn')
)
app_dev_role_name = Output(
    'AppDevRoleName',
    Value=Ref(dev_app.role)
)
# endregion
# region Test
app_test_media = Output(
    'AppTestMedia',
    Value=Ref(test_app.media_assets)
)
app_test_static = Output(
    'AppTestStatic',
    Value=Ref(test_app.static_assets)
)
app_test_distribution = Output(
    'AppTestDistribution',
    Value=Ref(test_app.distribution)
)
app_test_role_arn = Output(
    'AppTestRoleArn',
    Value=GetAtt(test_app.role, 'Arn')
)
app_test_role_name = Output(
    'AppTestRoleName',
    Value=Ref(test_app.role)
)
# endregion
# region Prod
app_prod_media = Output(
    'AppProdMedia',
    Value=Ref(prod_app.media_assets)
)
app_prod_static = Output(
    'AppProdStatic',
    Value=Ref(prod_app.static_assets)
)
app_prod_distribution = Output(
    'AppProdDistribution',
    Value=Ref(prod_app.distribution)
)
app_prod_role_arn = Output(
    'AppProdRoleArn',
    Value=GetAtt(prod_app.role, 'Arn')
)
app_prod_role_name = Output(
    'AppProdRoleName',
    Value=Ref(prod_app.role)
)
# endregion
