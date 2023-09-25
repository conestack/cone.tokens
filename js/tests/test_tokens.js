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
import {Tokens} from '../src/tokens.js';

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

QUnit.module.skip('Tokens', hooks => {
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

    QUnit.test('scan_token', assert => {
        let tokens = new Tokens(elem);
        // XXX
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