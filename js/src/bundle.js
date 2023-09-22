import $ from 'jquery';
import ts from 'treibstoff';
import {Tokens} from './tokens.js';
import {TokensOverview} from './tokens.js';

export * from './tokens.js';

$(function() {
    ts.ajax.register(Tokens.initialize, true);
    ts.ajax.register(TokensOverview.initialize, true);
});
