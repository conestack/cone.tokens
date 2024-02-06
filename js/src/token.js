import $ from 'jquery';
import ts from 'treibstoff';

export class Token {

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
            const button = $(this)
            button.on('click', function(e) {
                that.set_timerange(button.data('timerange-scope'));
            });
        });
        $('.btn-group.usage-count button', elem).each(function() {
            const button = $(this)
            button.on('click', function(e) {
                that.set_usage_count(button.data('usage-count'));
            });
        });
    }

    request_api(params) {
        const settings = this.settings;
        ts.http_request({
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
        let timerange, valid_from, valid_to;
        if (Object.keys(timeranges).includes(scope)) {
            timerange = timeranges[scope];
            let start = timerange.start.split(':');
            valid_from = new Date();
            valid_from.setHours(start[0], start[1], 0);
            let end = timerange.end.split(':');
            valid_to = new Date();
            valid_to.setHours(end[0], end[1], 0);
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
