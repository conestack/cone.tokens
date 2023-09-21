import os
import webresource as wr


resources_dir = os.path.join(os.path.dirname(__file__), 'static')
cone_tokens_resources = wr.ResourceGroup(
    name='cone.tokens-tokens',
    directory=resources_dir,
    path='tokens'
)
cone_tokens_resources.add(wr.ScriptResource(
    name='cone-tokens-js',
    depends='cone-app-protected-js',
    resource='cone.tokens.js',
    compressed='cone.tokens.min.js'
))
cone_tokens_resources.add(wr.StyleResource(
    name='cone-tokens-css',
    resource='cone.tokens.css',
    compressed='cone.tokens.min.css'
))


def configure_resources(config, settings):
    config.register_resource(cone_tokens_resources)
    config.set_resource_include('cone-tokens-js', 'authenticated')
    config.set_resource_include('cone-tokens-css', 'authenticated')
