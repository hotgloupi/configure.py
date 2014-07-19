import configure

@then('build variable {key} in {build_dir} equals {value}')
def impl(ctx, key, value, build_dir):
    assert ctx.configured
    env = configure.env.Env.load(build_dir + '/.build-env')
    assert env[key] == eval(value)

@then('project variable {key} equals {value}')
def impl(ctx, key, value):
    assert ctx.configured
    env = configure.env.Env.load('.config/.project-env')
    assert env[key] == eval(value)
