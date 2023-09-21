import $ from 'jquery';
import ts from 'treibstoff';
import {Tokens} from './tokens.js';

export * from './tokens.js';

$(function() {
    ts.ajax.register(Tokens.initialize, true);
});
