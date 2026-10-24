import $ from 'jquery';
import ts from 'treibstoff';
import { Token } from '../src/token.js';

QUnit.module('cone.tokens.bundle', (hooks) => {
    const ts_ajax_register_origin = ts.ajax.register;

    hooks.afterEach(() => {
        ts.ajax.register = ts_ajax_register_origin;
    });

    QUnit.test(
        'bundle exports tokens API and registers initializers on DOM ready',
        async (assert) => {
            const registered = [];
            ts.ajax.register = (func, instant) => {
                registered.push({ func, instant });
            };

            const bundle = await import('../src/bundle.js');
            // ready callbacks run in registration order, this one after the bundle's
            await new Promise((resolve) => $(resolve));

            assert.deepEqual(
                Object.keys(bundle).sort(),
                ['TokenScanner', 'TokensOverview'],
                'exported names',
            );
            assert.deepEqual(
                registered.map((reg) => reg.func),
                [
                    Token.initialize,
                    bundle.TokenScanner.initialize,
                    bundle.TokensOverview.initialize,
                ],
                'initializers registered',
            );
            assert.true(
                registered.every((reg) => reg.instant === true),
                'registered for instant execution',
            );
        },
    );
});
