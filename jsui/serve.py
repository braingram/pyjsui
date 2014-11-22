#!/usr/bin/env python

import inspect

import flask

import wsrpc


def rename(name):
    def wrap(func):
        func.func_name = name
        return func
    return wrap


def build_function_spec(o, s=None):
    if s is None:
        s = {}
    for k in dir(o):
        if k[0] == '_':
            continue
        a = getattr(o, k)
        if inspect.ismethod(a):
            arg_spec = inspect.getargspec(a)
            s[k] = arg_spec.args
        elif hasattr(a, '__init__'):
            ss = build_function_spec(a)
            if len(ss):
                s[k] = ss
    return s


def make_blueprint(spec):
    kwargs = {'url_prefix': '/{}'.format(spec['name'])}
    for k in ('static_folder', 'template_folder', 'static_url_path',
              'url_prefix'):
        if k in spec:
            kwargs[k] = spec[k]
    bp = flask.Blueprint(spec['name'], spec['name'], **kwargs)

    wsrpc.serve.register(
        spec['object'], spec['name'] + '/ws',
        encoder=spec.get('encoder', None), decoder=spec.get('decoder', None))

    if 'functions' not in spec:
        spec['functions'] = build_function_spec(spec['object'])

    @bp.route('/functions')
    def functions():
        return flask.jsonify(spec['functions'])
    if 'css' in spec:
        @bp.route('/css')
        def css():
            return flask.render_template_string(spec['css'], **spec)
    if 'js' in spec:
        @bp.route('/js')
        def js():
            return flask.render_template_string(spec['js'], **spec)
    if 'html' in spec:
        @bp.route('/html')
        def html():
            return flask.render_template_string(spec['html'], **spec)
    if 'template' in spec:
        @bp.route('/')
        def template():
            local_spec = spec.copy()
            for item in ('css', 'js', 'html'):
                if item in spec:
                    local_spec[item] = flask.render_template_string(
                        spec[item], **spec)
            return flask.render_template_string(
                spec['template'], **local_spec)
    if 'template_folder' in spec:
        @bp.route('/templates/<template>')
        def named_template(template):
            return flask.render_template(template, **spec)
    return bp


def register(spec):
    bp = make_blueprint(spec)
    wsrpc.serve.server.register_blueprint(bp)


def serve():
    wsrpc.serve.server.debug = True
    wsrpc.serve.serve()
