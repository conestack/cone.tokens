import $ from 'jquery';
import ts from 'treibstoff';

export class TokensOverview {

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
        this.size_input = $('<input type="number" />')
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
        this.token_size = 100; // percent
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

export class TokenScanner {

    static initialize(context) {
        $('.tokens-container', context).each(function() {
            new TokenScanner($(this));
        });
    }

    constructor(elem) {
        this.elem = elem;
        this.base_url = elem.data('base-url');
        this.button = $('.scan-token', elem);
        this._input_wrapper = null;
        this._input = null;

        this.scan_token = this.scan_token.bind(this);
        this.button.on('click', (e) => {
            this.scan_token();
        });
    }

    get active() {
        return this._input !== null;
    }

    set active(value) {
        if (value == this.value) {
            return;
        }
        let button = this.button;
        if (value) {
            let wrapper = this._input_wrapper = $('<div/>')
                .css('width', 0)
                .css('overflow', 'hidden');
            let input = this._input = $('<input type="text">');
            wrapper.append(input);
            this.elem.append(wrapper)
            button.removeClass('inactive').addClass('active');
            input[0].focus()
        } else {
            this._input_wrapper.remove();
            this._input_wrapper = null;
            this._input = null;
            button.removeClass('active').addClass('inactive');
        }
    }

    scan_token() {
        this.active = true;
        let input = this._input;
        input.one('change', () => {
            this.query_token(input.val());
        });
    }

    query_token(value) {
        let that = this;
        ts.ajax.request({
            url: `${this.base_url}/query_token`,
            params: {value: value},
            type: 'json',
            success: (data, status, request) => {
                if (data.success) {
                    if (!data.token) {
                        this.active = false;
                        ts.show_error('Token not exists');
                    } else {
                        ts.ajax.action({
                            name: 'layout',
                            selector: '#layout',
                            mode: 'replace',
                            url: `${this.base_url}/${data.token.uid}`,
                            params: {}
                        });
                    }
                } else {
                    ts.show_error(data.message);
                }
            },
            error: (request, status, error) => {
                ts.show_error(`Failed to request JSON API: ${error}`);
            }
        });
    }
}
