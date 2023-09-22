var cone_tokens = (function (exports, ts, jquery) {
    'use strict';

    class TokensOverview {
        static initialize(context) {
            jquery.$('.tokens-overview-container', context).each(function() {
                new TokensOverview(jquery.$(this));
            });
        }
        constructor(container) {
            this.container = container;
            this.tokens_elem = jquery.$('#tokens-overview', container);
            this.tokens = jquery.$('object.token_qr', this.tokens_elem);
            this.tokens_title = jquery.$('#tokens-overview-title', container);
            this.set_token_size = this.set_token_size.bind(this);
            this.size_input = jquery.$('<input />')
                .addClass('token-button')
                .on('change', this.set_token_size);
            this.size_input_label = jquery.$('<label />')
                .addClass('input-label')
                .text('Token Size');
            this.size_container = jquery.$('<div />')
                .addClass('token-size')
                .append(this.size_input_label)
                .append(this.size_input)
                .append(jquery.$('<span>%</span>'))
                .appendTo(this.tokens_title);
            if (this.tokens.length) {
                this.original_size = this.tokens[0].attr('width');
            } else {
                this.original_size = 256;
            }
            this.token_size = 100;
        }
        get token_size() {
            return this._token_size;
        }
        set token_size(size) {
            if (!size) {
                size = 100;
            }
            let px_value = this.original_size * (size / 100);
            this.tokens_elem.css(
                'grid-template-columns',
                `repeat( auto-fit, minmax(${px_value}px, 1fr) )`
            );
            this.tokens.each(function() {
                let elem = jquery.$(this);
                elem.attr('width', `${px_value}px`);
                elem.attr('height', `${px_value}px`);
            });
            if (!this.size_input.val()) {
                this.size_input.val(size);
            }
            this._token_size = size;
        }
        set_token_size(evt) {
            evt.preventDefault();
            let size = this.size_input.val();
            this.token_size = size;
        }
    }
    class Tokens {
        static initialize(context) {
            jquery.$('.tokens-container', context).each(function() {
                new Tokens(jquery.$(this));
            });
        }
        constructor(elem) {
            this.elem = elem;
            this.token_uid_elem = jquery.$('[name=token-uid]', elem);
            this.scan_token_elem = jquery.$('.scan-token', elem);
            this.scan_token = this.scan_token.bind(this);
            this.scan_token_elem.on('click', (e) => {
                this.scan_token();
            });
        }
        scan_token() {
            uid_elem = this.token_uid_elem;
            uid_elem.val('');
            uid_elem[0].focus();
            uid_elem.on('change', () => {
                console.log('change');
                let val = uid_elem.val();
                if (val.length == 36) {
                    uid_elem.val('');
                    uid_elem.off('change');
                }        });
        }
    }

    $(function() {
        ts.ajax.register(Tokens.initialize, true);
        ts.ajax.register(TokensOverview.initialize, true);
    });

    exports.Tokens = Tokens;
    exports.TokensOverview = TokensOverview;

    Object.defineProperty(exports, '__esModule', { value: true });

    return exports;

})({}, ts, jQuery);
