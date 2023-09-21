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
            this.token_uid_elem = $('[name=token-uid]', elem);
            this.scan_token_elem = $('.scan-token', elem);
            this.scan_token = this.scan_token.bind(this);
            this.scan_token_elem.on('click', (e) => {
                this.scan_token();
            });
        }
        scan_token() {
            this.token_uid_elem.val('');
            this.token_uid_elem[0].focus();
            this.token_uid_elem.on('change', () => {
                console.log('change');
                let val = this.token_uid_elem.val();
                if (val.length == 36) {
                    this.token_uid_elem.val('');
                    this.token_uid_elem.off('change');
                }        });
        }
    }

    $$1(function() {
        ts.ajax.register(Tokens.initialize, true);
    });

    exports.Tokens = Tokens;

    Object.defineProperty(exports, '__esModule', { value: true });

    return exports;

})({}, jQuery, ts);
