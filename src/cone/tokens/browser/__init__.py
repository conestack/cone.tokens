import os
import webresource as wr

resources_dir = os.path.join(os.path.dirname(__file__), 'static')
tokens_resources = wr.ResourceGroup(
    name='tokens',
    directory=resources_dir,
    path='tokens'
)
tokens_resources.add(wr.StyleResource(
    name='tokens-css',
    resource='tokens.css'
))

def configure_resources(config, settings):
    config.register_resource(tokens_resources)
    config.set_resource_include('tokens-css', 'authenticated')
