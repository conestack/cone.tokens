//
// SQUAREWAVE COMPUTING
//
// 2012-2023 Squarewave Computing, Robert Niederreiter
// All Rights Reserved
//
// NOTICE: All information contained herein is, and remains the property of
// Squarewave Computing and its suppliers, if any. The intellectual and
// technical concepts contained herein are proprietary to Squarewave Computing
// and its suppliers.
//

import $ from 'jquery';
import ts from 'treibstoff';
import { TokenScanner, TokensOverview } from '../src/tokens.js';

QUnit.module('TokensOverview', (hooks) => {
    let elem, tokens_filter, tokens_elem, start_input, end_input;
    hooks.beforeEach(() => {
        elem = $('<div />').addClass('tokens-overview-container').appendTo('body');
        tokens_elem = $('<div id="tokens-overview" />').appendTo(elem);
        // filter
        tokens_filter = $('<div id="tokens-filter-options" />').appendTo(elem);
        $('<input name="token-size" />').appendTo(tokens_filter);
        start_input = $('<input name="start" />').appendTo(tokens_filter);
        end_input = $('<input name="end" />').appendTo(tokens_filter);
        // add tokens
        const add_tokens = $('<div id="tokens-create-options" />').appendTo(elem);
        const add_tokens_container = $('<div class="add-tokens" />').appendTo(add_tokens);
        $('<input name="amount" />').appendTo(add_tokens_container);
    });
    hooks.afterEach(() => {
        elem.empty().remove();
        elem = null;
        tokens_elem = null;
        tokens_filter = null;
    });

    QUnit.test('initialize', (assert) => {
        TokensOverview.initialize(elem.parent());

        // token size input gets initialized by the created TokensOverview instance
        assert.strictEqual($('input[name="token-size"]', elem).val(), '100');
    });

    QUnit.test('constructor no tokens', (assert) => {
        const ov = new TokensOverview(elem);
        assert.deepEqual(ov.container, elem);
        assert.strictEqual(ov.tokens.length, 0);
        assert.strictEqual(ov.original_size, 256);
        assert.strictEqual(ov.token_size, 100);
    });

    QUnit.test('constructor with tokens', (assert) => {
        create_tokens(tokens_elem, 2);
        const ov = new TokensOverview(elem);
        assert.deepEqual(ov.container, elem);
        assert.strictEqual(ov.tokens.length, 2);
        assert.strictEqual(ov.original_size, 200);
        assert.strictEqual(ov.token_size, 100);
    });

    QUnit.test('get/set token_size', (assert) => {
        create_tokens(tokens_elem, 1);
        const ov = new TokensOverview(elem);
        assert.strictEqual(ov.token_size, 100);
        assert.strictEqual(ov.size_input.val(), '100');

        ov.token_size = 50;
        assert.strictEqual(ov.token_size, 50);
        assert.strictEqual(
            ov.tokens_elem.css('grid-template-columns'),
            'repeat(auto-fit, minmax(100px, 1fr))',
        );
        assert.strictEqual($(ov.tokens[0]).attr('width'), '100px');
        assert.strictEqual($(ov.tokens[0]).attr('height'), '100px');

        // unset token size
        ov.token_size = '';
        assert.strictEqual(ov.token_size, 100);
    });

    QUnit.test('set_token_size', (assert) => {
        create_tokens(tokens_elem, 1);
        const ov = new TokensOverview(elem);
        ov.size_input.val(200);
        ov.size_input.trigger('change');
        assert.strictEqual(ov.token_size, '200');
        assert.strictEqual($(ov.tokens[0]).attr('width'), '400px');
        assert.strictEqual($(ov.tokens[0]).attr('height'), '400px');
    });

    QUnit.test('filter_tokens', (assert) => {
        // patch ts.http_request and action
        const original_ts_action = ts.ajax.action;
        ts.ajax.action = (opts) => {
            assert.step('ajax_success');
            assert.step(`start: ${opts.params.start}`);
            assert.step(`end: ${opts.params.end}`);
        };

        // init TokensOverview
        elem.data('token-settings', { base_url: 'https://tld.com' });
        const ov = new TokensOverview(elem);

        // filter tokens
        ov.filter_tokens({ preventDefault: () => {} });
        assert.verifySteps(['ajax_success', 'start: ', 'end: ']);

        // start and end values
        start_input.val('28.09.2023');
        end_input.val('30.09.2023');
        ov.filter_tokens({ preventDefault: () => {} });
        assert.verifySteps(['ajax_success', 'start: 28.09.2023', 'end: 30.09.2023']);

        // reset ts ajax
        ts.ajax.action = original_ts_action;
        assert.ok(true);
    });

    QUnit.test('add_tokens', (assert) => {
        let force_success = false;
        let force_data_success = false;
        const data_token = false;

        // patch ts.http_request and action
        const original_ts_request = ts.http_request;
        const original_ts_action = ts.ajax.action;
        const original_ts_error = ts.show_error;
        ts.http_request = (opts) => {
            if (force_success) {
                if (force_data_success) {
                    opts.success({
                        success: force_data_success,
                        token: data_token,
                    });
                } else {
                    opts.success({
                        success: force_data_success,
                        message: 'ajax_fail',
                    });
                }
            } else {
                opts.error(null, null, '');
            }
        };
        ts.ajax.action = (opts) => {
            assert.step('ajax_success');
            assert.step(opts.url);
        };
        ts.show_error = (err) => {
            assert.step(err);
        };

        // init TokensOverview
        elem.data('token-settings', { base_url: 'https://tld.com' });
        const ov = new TokensOverview(elem);

        // no input value
        ov.add_tokens();
        assert.verifySteps([]);

        // ajax failure
        $(ov.add_tokens_input).val('1');
        ov.add_tokens();
        assert.verifySteps(['Failed to request JSON API: ']);

        // force success
        force_success = true;
        ov.add_tokens();
        assert.verifySteps(['ajax_fail']);

        // force data success
        force_data_success = true;
        ov.add_tokens();
        assert.verifySteps(['ajax_success', 'https://tld.com']);

        // amount != count
        $(ov.add_tokens_input).val('2');
        ov.add_tokens();
        assert.verifySteps(['ajax_success', 'https://tld.com']);

        // reset ts ajax
        ts.http_request = original_ts_request;
        ts.ajax.action = original_ts_action;
        ts.show_error = original_ts_error;
    });

    QUnit.test('delete_tokens', (assert) => {
        create_tokens(tokens_elem, 2);

        let force_success = false;
        let force_data_success = false;

        // patch ts.http_request and action
        const original_ts_request = ts.http_request;
        const original_ts_action = ts.ajax.action;
        const original_ts_error = ts.show_error;
        const original_ts_message = ts.show_message;
        ts.http_request = (opts) => {
            if (force_success) {
                if (force_data_success) {
                    opts.success({
                        success: force_data_success,
                        message: opts.params.token_uids,
                    });
                } else {
                    opts.success({
                        success: force_data_success,
                        message: 'ajax_fail',
                    });
                }
            } else {
                opts.error(null, null, '');
            }
        };
        ts.ajax.action = (opts) => {
            assert.step('ajax_success');
            assert.step(opts.url);
        };
        ts.show_error = (err) => {
            assert.step(err);
        };
        ts.show_message = (opts) => {
            assert.step(opts.message);
        };

        // init TokensOverview
        elem.data('token-settings', { base_url: 'https://tld.com' });
        const ov = new TokensOverview(elem);

        // ajax failure
        ov.delete_tokens();
        $('.modal button.ok').trigger('click');
        assert.verifySteps(['Failed to request JSON API: ']);

        // force success
        force_success = true;
        ov.delete_tokens();
        $('.modal button.ok').trigger('click');
        assert.verifySteps(['ajax_fail']);

        // force data success
        force_data_success = true;
        const token_1_uid = $($('.token_qr')[0]).data('token-uid');
        const token_2_uid = $($('.token_qr')[1]).data('token-uid');
        ov.delete_tokens();
        $('.modal button.ok').trigger('click');
        assert.verifySteps([
            'ajax_success',
            'https://tld.com',
            `["${token_1_uid}","${token_2_uid}"]`,
        ]);

        // reset ts ajax
        ts.http_request = original_ts_request;
        ts.ajax.action = original_ts_action;
        ts.show_error = original_ts_error;
        ts.show_message = original_ts_message;
    });
});

QUnit.module('TokenScanner', (hooks) => {
    let elem, btn, original_ts, original_console_log;
    hooks.beforeEach(() => {
        elem = $('<div />').addClass('tokens-container').appendTo('body');
        btn = $('<button />').addClass('scan-token').appendTo(elem);
        original_ts = {
            http_request: ts.http_request,
            action: ts.ajax.action,
            show_error: ts.show_error,
            show_dialog: ts.show_dialog,
        };
        original_console_log = console.log;
    });
    hooks.afterEach(() => {
        ts.http_request = original_ts.http_request;
        ts.ajax.action = original_ts.action;
        ts.show_error = original_ts.show_error;
        ts.show_dialog = original_ts.show_dialog;
        console.log = original_console_log;
        elem.empty().remove();
        elem = null;
        btn = null;
    });

    QUnit.test('initialize', (assert) => {
        TokenScanner.initialize(elem.parent());

        // scan button is bound by the created TokenScanner instance
        btn.trigger('click');
        assert.true(btn.hasClass('active'));
        assert.strictEqual($('input[type="text"]', elem).length, 1);
    });

    QUnit.test('constructor', (assert) => {
        elem.data('base-url', 'https://tld.com');
        const tsc = new TokenScanner(elem);
        assert.strictEqual(tsc.base_url, 'https://tld.com');
        assert.strictEqual(tsc._input_wrapper, null);
        assert.strictEqual(tsc._input, null);
    });

    QUnit.test('get/set active', (assert) => {
        elem.data('base-url', 'https://tld.com');
        const tsc = new TokenScanner(elem);
        // initial
        assert.strictEqual(tsc.active, false);
        // set value true
        tsc.active = true;
        assert.ok(tsc._input_wrapper);
        assert.ok(tsc._input);
        assert.true(btn.hasClass('active'));

        // set value false
        tsc.active = false;
        assert.strictEqual(tsc._input, null);
        assert.strictEqual(tsc._input_wrapper, null);
        assert.true(btn.hasClass('inactive'));
    });

    QUnit.test('scan_token', (assert) => {
        elem.data('base-url', 'https://tld.com');
        const tsc = new TokenScanner(elem);
        tsc.query_token = (val) => {
            assert.step(`query_token ${val}`);
        };
        assert.strictEqual(tsc.active, false);

        // scan token
        tsc.button.trigger('click');
        assert.strictEqual(tsc.active, true);
        assert.ok(tsc._input);
        tsc._input.val('token-1');
        tsc._input.trigger('change');
        assert.verifySteps(['query_token token-1']);
    });

    QUnit.test('query_token', (assert) => {
        let force_success = false;

        // patch ts.http_request
        ts.http_request = (opts) => {
            if (force_success) {
                opts.success({
                    success: false,
                    message: 'ajax_fail',
                });
            } else {
                opts.error(null, null, '');
            }
        };
        ts.show_error = (err) => {
            assert.step(err);
        };

        // init TokenScanner
        elem.data('base-url', 'https://tld.com');
        const tsc = new TokenScanner(elem);
        tsc.active = true;

        // ajax failure
        tsc.query_token();
        assert.verifySteps(['Failed to request JSON API: ']);

        // ajax success, not data success
        force_success = true;
        tsc.query_token();
        assert.verifySteps(['ajax_fail']);
    });

    QUnit.test('query_token loads existing token', (assert) => {
        ts.http_request = (opts) => {
            assert.step(`request ${opts.url} ${opts.params.value}`);
            opts.success({ success: true, token: { uid: 'token_uid_1' } });
        };
        ts.ajax.action = (opts) => {
            assert.step(`action ${opts.name} ${opts.selector} ${opts.mode} ${opts.url}`);
        };
        console.log = (msg) => {
            assert.step(msg);
        };

        elem.data('base-url', 'https://tld.com');
        const tsc = new TokenScanner(elem);
        tsc.active = true;

        tsc.query_token('token-1');
        assert.verifySteps([
            'request https://tld.com/query_token token-1',
            'load token: token_uid_1',
            'action layout #layout replace https://tld.com/token_uid_1',
        ]);
    });

    QUnit.test('query_token creates not existing token', (assert) => {
        ts.http_request = (opts) => {
            assert.step(`request ${opts.url} ${opts.params.value} ${opts.method}`);
            if (opts.url.endsWith('/query_token')) {
                opts.success({ success: true, token: null });
            } else {
                opts.success({ success: true, token_uid: 'token_uid_2' });
            }
        };
        ts.show_dialog = (opts) => {
            assert.step(`dialog ${opts.title} ${opts.message}`);
            opts.on_confirm();
        };
        ts.ajax.action = (opts) => {
            assert.step(`action ${opts.url}`);
        };
        console.log = (msg) => {
            assert.step(msg);
        };

        elem.data('base-url', 'https://tld.com');
        const tsc = new TokenScanner(elem);
        tsc.active = true;

        tsc.query_token('token-2');
        assert.false(tsc.active);
        assert.verifySteps([
            'request https://tld.com/query_token token-2 undefined',
            'dialog Token not exists? Do you want to create it?',
            'request https://tld.com/add_token token-2 POST',
            'load token: token_uid_2',
            'action https://tld.com/token_uid_2',
        ]);
    });

    QUnit.test('query_token create token failure', (assert) => {
        let add_token_response;
        ts.http_request = (opts) => {
            if (opts.url.endsWith('/query_token')) {
                opts.success({ success: true, token: null });
            } else {
                add_token_response(opts);
            }
        };
        ts.show_dialog = (opts) => {
            opts.on_confirm();
        };
        ts.show_error = (err) => {
            assert.step(err);
        };

        elem.data('base-url', 'https://tld.com');
        const tsc = new TokenScanner(elem);

        // not data success
        add_token_response = (opts) => {
            opts.success({ success: false, message: 'add_token_fail' });
        };
        tsc.active = true;
        tsc.query_token('token-3');
        assert.verifySteps(['add_token_fail']);

        // ajax failure
        add_token_response = (opts) => {
            opts.error(null, null, 'Server Error');
        };
        tsc.active = true;
        tsc.query_token('token-3');
        assert.verifySteps(['Failed to request JSON API: Server Error']);
    });
});

function create_tokens(container, count) {
    for (let i = 0; i < count; i++) {
        const uid = crypto.randomUUID();
        $('<object />')
            .addClass('token_qr')
            .attr('width', '200px')
            .attr('height', '200px')
            .data('token-uid', uid)
            .appendTo(container);
    }
}
