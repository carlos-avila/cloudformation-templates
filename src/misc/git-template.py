#!/usr/bin/env python3

from troposphere import codecommit, GetAtt, Sub
from troposphere import Template, Output

template = Template("""
Manage a Git repository with CodeCommit.

Template: git-template
Author: Carlos Avila <cavila@mandelbrew.com>
""")

# region Resources
repository = template.add_resource(codecommit.Repository(
    'Repository',
    RepositoryName=Sub('${AWS::StackName}')
))
# endregion

# region Outputs
template.add_output(
    Output('CloneUrlHttp', Value=GetAtt(repository, 'CloneUrlHttp'))
)
template.add_output(
    Output('CloneUrlSsh', Value=GetAtt(repository, 'CloneUrlSsh'))
)
# endregion

if __name__ == '__main__':
    print(template.to_json())
