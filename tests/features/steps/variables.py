import configure

@then('build variable {key} equals {value}')
def impl(ctx, key, value):
    assert ctx.configured
    env = configure.env.Env.load('build/.build-env')
    assert env[key] == eval(value)
