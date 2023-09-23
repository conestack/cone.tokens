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
            usage_count: usage_count ? usage_count : '-1'
        });
    }
}
