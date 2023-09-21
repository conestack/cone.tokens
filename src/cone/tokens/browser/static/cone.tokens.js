var cone_tokens = (function (exports, $$1, ts) {
    'use strict';

    class Tokens {
        static initialize(context) {
            $('.tokens-container', context).each(function() {
                new Tokens($(this));
            });
        }
        constructor(elem) {
            this.elem = elem;
            console.log(this);
        }
    }

    $$1(function() {
        ts.ajax.register(Tokens.initialize, true);
    });

    exports.Tokens = Tokens;

    Object.defineProperty(exports, '__esModule', { value: true });

    return exports;

})({}, jQuery, ts);
