import $ from 'jquery';
import ts from 'treibstoff';
import {Token} from './token.js';
import {TokenScanner} from './tokens.js';
import {TokensOverview} from './tokens.js';

export * from './tokens.js';

$(function() {
    ts.ajax.register(Token.initialize, true);
    ts.ajax.register(TokenScanner.initialize, true);
    ts.ajax.register(TokensOverview.initialize, true);
});
