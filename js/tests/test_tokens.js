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
        elem.empty();
        elem = null;
        tokens_elem = null;
        tokens_title = null;
    });

    QUnit.test('constructor no tokens', assert => {
        let ov = new TokensOverview(elem);
        // assert.deepEqual(ov.container, elem);
        // assert.deepEqual(ov.tokens_title, tokens_title);
        assert.strictEqual(ov.tokens.length, 0);
    });
});

function create_tokens(container, count) {
    for (let i = 0; i < count; i++) {
        let token = $('<object />')
            .addClass('token-qr')
            .appendTo(container);
    }
}