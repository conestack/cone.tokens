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
import {TokensOverview} from '../src/tokens.js';
import {TokenScanner} from '../src/tokens.js';
import ts from 'treibstoff';

QUnit.module('TokensOverview', hooks => {
    let elem,
        tokens_title,
        tokens_elem;
    hooks.beforeEach(() => {
        elem = $('<div />')
            .addClass('tokens-overview-container')
            .appendTo('body');
        tokens_title = $('<div id="tokens-overview-title" />')
            .appendTo(elem);
        tokens_elem = $('<div id="tokens-overview" />')
            .appendTo(elem);
    });
    hooks.afterEach(() => {
        elem.empty().remove();
        elem = null;
        tokens_elem = null;
        tokens_title = null;
    });

    QUnit.test('constructor no tokens', assert => {
        let ov = new TokensOverview(elem);
        assert.deepEqual(ov.container, elem);
        assert.strictEqual(ov.tokens.length, 0);
        assert.strictEqual(ov.original_size, 256);
        assert.strictEqual(ov.token_size, 100);
    });

    QUnit.test('constructor with tokens', assert => {
        create_tokens(tokens_elem, 2);
        let ov = new TokensOverview(elem);
        assert.deepEqual(ov.container, elem);
        assert.strictEqual(ov.tokens.length, 2);
        assert.strictEqual(ov.original_size, 200);
        assert.strictEqual(ov.token_size, 100);
    });

    QUnit.test('get/set token_size', assert => {
        create_tokens(tokens_elem, 1);
        let ov = new TokensOverview(elem);
        assert.strictEqual(ov.token_size, 100);
        assert.strictEqual(ov.size_input.val(), '100');

        ov.token_size = 50;
        assert.strictEqual(ov.token_size, 50);
        assert.strictEqual(
            ov.tokens_elem.css('grid-template-columns'),
            'repeat(auto-fit, minmax(100px, 1fr))'
        );
        assert.strictEqual($(ov.tokens[0]).attr('width'), '100px');
        assert.strictEqual($(ov.tokens[0]).attr('height'), '100px');

        // unset token size
        ov.token_size = '';
        assert.strictEqual(ov.token_size, 100);
    });

    QUnit.test('set_token_size', assert => {
        create_tokens(tokens_elem, 1);
        let ov = new TokensOverview(elem);
        ov.size_input.val(200);
        ov.size_input.trigger('change');
        assert.strictEqual(ov.token_size, '200');
        assert.strictEqual($(ov.tokens[0]).attr('width'), '400px');
        assert.strictEqual($(ov.tokens[0]).attr('height'), '400px');
    });
});

QUnit.module('TokenScanner', hooks => {
    let elem,
        btn,
        input;
    hooks.beforeEach(() => {
        elem = $('<div />')
            .addClass('tokens-container')
            .appendTo('body');
        btn = $('<button />')
            .addClass('scan-token')
            .appendTo(elem);
        input = $('<input />')
            .attr('name', 'token-uid')
            .attr('type', 'text')
            .appendTo(elem);
    });
    hooks.afterEach(() => {
        elem.empty().remove();
        elem = null;
        btn = null;
        input = null;
    });

    QUnit.test('constructor', assert => {
        elem.data('base-url', 'https://tld.com');
        let tsc = new TokenScanner(elem);
        assert.strictEqual(tsc.base_url, 'https://tld.com');
        assert.strictEqual(tsc._input_wrapper, null);
        assert.strictEqual(tsc._input, null);
    });

    QUnit.test('get/set active', assert => {
        elem.data('base-url', 'https://tld.com');
        let tsc = new TokenScanner(elem);
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

    QUnit.test('scan_token', assert => {
        elem.data('base-url', 'https://tld.com');
        let tsc = new TokenScanner(elem);
        tsc.query_token = (val) => {
            assert.step('query_token ' + val);
        }
        assert.strictEqual(tsc.active, false);

        // scan token
        tsc.button.trigger('click');
        assert.strictEqual(tsc.active, true);
        assert.ok(tsc._input);
        tsc._input.val('token-1');
        tsc._input.trigger('change');
        assert.verifySteps(['query_token token-1']);
    });

    QUnit.test('query_token', assert => {
        let force_success = false;
        let force_data_success = false;
        let data_token = false;

        // patch ts.ajax.request and action
        const original_ts_request = ts.ajax.request;
        const original_ts_action = ts.ajax.action;
        const original_ts_error = ts.show_error;
        ts.ajax.request = function(opts) {
            if (force_success) {
                if (force_data_success) {
                    opts.success({
                        success: force_data_success,
                        token: data_token
                    });
                } else {
                    opts.success({
                        success: force_data_success,
                        message: 'ajax_fail'
                    });
                }
            } else {
                opts.error(null, null, '');
            }
        }
        ts.ajax.action = function(opts) {
            assert.step('ajax_success');
            assert.step(opts.url);
        }
        ts.show_error = function(err) {
            assert.step(err);
        }

        // init TokenScanner
        elem.data('base-url', 'https://tld.com');
        let tsc = new TokenScanner(elem);
        tsc.active = true;

        // ajax failure
        tsc.query_token();
        assert.verifySteps(['Failed to request JSON API: ']);

        // ajax success, not data success
        force_success = true;
        tsc.query_token();
        assert.verifySteps(['ajax_fail']);

        // ajax success, not data.token
        force_data_success = true;
        tsc.query_token();
        assert.verifySteps(['Token not exists']);

        // ajax success with data.token
        data_token = {uid: 'token_uid_1'};
        tsc.query_token();
        assert.verifySteps([
            'ajax_success',
            'https://tld.com/token_uid_1'
        ]);

        // reset ts ajax
        ts.ajax.request = original_ts_request;
        ts.ajax.action = original_ts_action;
        ts.show_error = original_ts_error;
    });
});

function create_tokens(container, count) {
    for (let i = 0; i < count; i++) {
        let token = $('<object />')
            .addClass('token_qr')
            .attr('width', '200px')
            .attr('height', '200px')
            .appendTo(container);
    }
}