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
        this.token_settings = this.container.data('token-settings');

        // add tokens
        this.add_tokens_container = $('.add-tokens', this.tokens_title);
        this.add_tokens_input = $(
            'input[name="amount"]',
            this.add_tokens_container
        );
        this.add_tokens_btn = $(
            'button[name="add-tokens"]',
            this.add_tokens_container
        );
        this.add_tokens = this.add_tokens.bind(this);
        this.add_tokens_btn.on('click', this.add_tokens);

        // date filter
        this.start = $('input[name="start"]', this.tokens_title)
            .addClass('datepicker')
            .data('date-locale', 'de');
        this.end = $('input[name="end"]', this.tokens_title)
            .addClass('datepicker')
            .data('date-locale', 'de');
        this.filter = $('button[name="filter"]', this.tokens_title);
        this.filter_tokens = this.filter_tokens.bind(this);
        this.filter.on('click', this.filter_tokens);

        // delete tokens
        this.delete_tokens_container = $('.delete-tokens', this.tokens_title);
        this.delete_tokens_btn = $(
            'button[name="delete-tokens"]',
            this.delete_tokens_container
        );
        this.delete_tokens = this.delete_tokens.bind(this);
        this.delete_tokens_btn.on('click', this.delete_tokens);

        this.set_token_size = this.set_token_size.bind(this);
        this.size_input = $('input[name="token-size"]', this.tokens_title);
        this.size_input.on('change', this.set_token_size);
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

    filter_tokens(evt) {
        evt.preventDefault();
        let params = {
            start: this.start.val(),
            end: this.end.val()
        };
        ts.ajax.action({
            name: 'tokens_overview',
            mode: 'inner',
            selector: '#content',
            url: this.token_settings.base_url,
            params: params
        });
    }

    add_tokens(evt) {
        const base_url = this.token_settings.base_url;
        function add(amount, count) {
            ts.http_request({
                url: `${base_url}/add_token`,
                params: {},
                type: 'json',
                method: 'POST',
                success: (data, status, request) => {
                    if (data.success) {
                        count += 1;
                        if (amount === count) {
                            ts.ajax.action({
                                name: 'tokens_overview',
                                selector: '#content',
                                mode: 'inner',
                                url: base_url,
                                params: {}
                            });
                        } else {
                            add(amount, count);
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
        let amount = this.add_tokens_input.val();
        if (!amount) {
            return;
        } else {
            amount = parseInt(amount);
        }
        add(amount, 0);
    }

    delete_tokens(evt) {
        const base_url = this.token_settings.base_url;

        ts.show_dialog({
            title: 'Delete tokens?',
            message: 'Do you really want to delete selected tokens?',
            on_confirm: () => {
                let uids = [];
                for (let token of this.tokens) {
                    let uid = $(token).data('token-uid');
                    uids.push(uid);
                }
                ts.http_request({
                    url: `${base_url}/delete_tokens`,
                    params: {token_uids: JSON.stringify(uids)},
                    type: 'json',
                    method: 'POST',
                    success: (data, status, request) => {
                        if (data.success) {
                            ts.ajax.action({
                                name: 'tokens_overview',
                                selector: '#content',
                                mode: 'inner',
                                url: base_url,
                                params: {}
                            });
                            ts.show_message({message: data.message, flavor:''})
                        } else {
                            ts.show_error(data.message);
                        }
                    },
                    error: (request, status, error) => {
                        ts.show_error(`Failed to request JSON API: ${error}`);
                    }
                });
            }
        });
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
            this.elem.append(wrapper);
            button.removeClass('inactive').addClass('active');
            input[0].focus();
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

    load_token(token_uid) {
        console.log('load token: ' + token_uid);
        ts.ajax.action({
            name: 'layout',
            selector: '#layout',
            mode: 'replace',
            url: `${this.base_url}/${token_uid}`,
            params: {}
        });
    }

    query_token(value) {
        ts.http_request({
            url: `${this.base_url}/query_token`,
            params: {value: value},
            type: 'json',
            success: (data, status, request) => {
                if (data.success) {
                    if (!data.token) {
                        this.active = false;
                        ts.show_dialog({
                            title: 'Token not exists?',
                            message: 'Do you want to create it?',
                            on_confirm: () => {
                                ts.http_request({
                                    url: `${this.base_url}/add_token`,
                                    params: {value: value},
                                    type: 'json',
                                    method: 'POST',
                                    success: (data, status, request) => {
                                        if (data.success) {
                                            this.load_token(data.token_uid);
                                        } else {
                                            ts.show_error(data.message);
                                        }
                                    },
                                    error: (request, status, error) => {
                                        ts.show_error(`Failed to request JSON API: ${error}`);
                                    }
                                });
                            }
                        });
                    } else {
                        this.load_token(data.token.uid);
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
