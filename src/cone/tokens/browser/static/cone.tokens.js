var cone_tokens = (function (exports, $, ts) {
    'use strict';

    class Token {
        static initialize(context) {
            $('.token', context).each(function() {
                new Token($(this));
            });
        }
        constructor(elem) {
            this.elem = elem;
            this.settings = elem.data('token-settings');
            const that = this;
            $('.btn-group.timeranges button', elem).each(function() {
                const button = $(this);
                button.on('click', function(e) {
                    that.set_timerange(button.data('timerange-scope'));
                });
            });
            $('.btn-group.usage-count button', elem).each(function() {
                const button = $(this);
                button.on('click', function(e) {
                    that.set_usage_count(button.data('usage-count'));
                });
            });
        }
        request_api(params) {
            const settings = this.settings;
            ts.ajax.request({
                url: `${settings.base_url}/update_token`,
                params: params,
                type: 'json',
                method: 'POST',
                success: (data, status, request) => {
                    if (data.success) {
                        ts.ajax.action({
                            name: 'content',
                            selector: '#content',
                            mode: 'inner',
                            url: `${settings.base_url}`,
                            params: {}
                        });
                    } else {
                        ts.show_error(data.message);
                    }
                },
                error: (request, status, error) => {
                    ts.show_error(`Failed to request JSON API: ${error}`);
                }
            });
        }
        set_timerange(scope) {
            const settings = this.settings,
                timeranges = settings.timeranges;
            let valid_from, valid_to;
            if (scope == 'morning') {
                const morning = timeranges.morning;
                valid_from = new Date();
                valid_from.setHours(morning.from.hour, morning.from.minute, 0);
                valid_to = new Date();
                valid_to.setHours(morning.to.hour, morning.to.minute, 0);
            } else if (scope == 'afternoon') {
                const afternoon = timeranges.afternoon;
                valid_from = new Date();
                valid_from.setHours(afternoon.from.hour, afternoon.from.minute, 0);
                valid_to = new Date();
                valid_to.setHours(afternoon.to.hour, afternoon.to.minute, 0);
            } else if (scope == 'today') {
                const today = timeranges.today;
                valid_from = new Date();
                valid_from.setHours(today.from.hour, today.from.minute, 0);
                valid_to = new Date();
                valid_to.setHours(today.to.hour, today.to.minute, 0);
            }
            function iso_date(date) {
                if (date) {
                    date = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
                }
                return date ? date.toISOString() : '';
            }
            this.request_api({
                valid_from: iso_date(valid_from),
                valid_to: iso_date(valid_to),
            });
        }
        set_usage_count(usage_count) {
            this.request_api({
                usage_count: usage_count
            });
        }
    }

    class TokensOverview {
        static initialize(context) {
            $('.tokens-overview-container', context).each(function() {
                new TokensOverview($(this));
            });
        }
        constructor(container) {
            this.container = container;
            this.tokens_elem = $('#tokens-overview', container);
            this.tokens = $('object.token_qr', this.tokens_elem);
            this.tokens_title = $('#tokens-overview-title', container);
            this.set_token_size = this.set_token_size.bind(this);
            this.size_input = $('<input />')
                .addClass('token-button')
                .on('change', this.set_token_size);
            this.size_input_label = $('<label />')
                .addClass('input-label')
                .text('Token Size');
            this.size_container = $('<div />')
                .addClass('token-size')
                .append(this.size_input_label)
                .append(this.size_input)
                .append($('<span>%</span>'))
                .appendTo(this.tokens_title);
            if (this.tokens.length) {
                this.original_size = parseInt($(this.tokens[0]).attr('width'));
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
                let elem = $(this);
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
    class TokenScanner {
        static initialize(context) {
            $('.tokens-container', context).each(function() {
                new TokenScanner($(this));
            });
        }
        constructor(elem) {
            this.elem = elem;
            this.button = $('.scan-token', elem);
            this.scan_token = this.scan_token.bind(this);
            this.button.on('click', (e) => {
                this.scan_token();
            });
        }
        scan_token() {
            let button = this.button,
                wrapper = $('<div/>').css('width', 0).css('overflow', 'hidden'),
                input = $('<input type="text">');
            wrapper.append(input);
            this.elem.append(wrapper);
            button.removeClass('inactive').addClass('active');
            input[0].focus();
            input.one('change', () => {
                let val = input.val();
                console.log(val);
                wrapper.remove();
                button.removeClass('active').addClass('inactive');
            });
        }
    }

    $(function() {
        ts.ajax.register(Token.initialize, true);
        ts.ajax.register(TokenScanner.initialize, true);
        ts.ajax.register(TokensOverview.initialize, true);
    });

    exports.TokenScanner = TokenScanner;
    exports.TokensOverview = TokensOverview;

    Object.defineProperty(exports, '__esModule', { value: true });

    return exports;

})({}, jQuery, ts);
