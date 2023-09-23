import $ from 'jquery';
import ts from 'treibstoff';
import {Token} from './token.js';
import {Tokens} from './tokens.js';
import {TokensOverview} from './tokens.js';

export * from './tokens.js';

$(function() {
    ts.ajax.register(Token.initialize, true);
    ts.ajax.register(Tokens.initialize, true);
    ts.ajax.register(TokensOverview.initialize, true);
});
