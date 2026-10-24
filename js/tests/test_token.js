//
// SQUAREWAVE COMPUTING
//
// 2012-2023 Squarewave Computing, Robert Niederreiter
// All Rights Reserved
//
// NOTICE: All information contained herein is, and remains the property of
// Squarewave Computing and its suppliers, if any. The intellectual and
// technical concepts contained herein are proprietary to Squarewave Computing
// and its suppliers.
//

import $ from 'jquery';
import ts from 'treibstoff';
import { Token } from '../src/token.js';

QUnit.module('Token', (hooks) => {
    let elem, timeranges, usagecount, original_ts_request;

    hooks.beforeEach(() => {
        elem = $('<div />').addClass('token').appendTo('body');
        timeranges = $('<div />').addClass('btn-group timeranges').appendTo(elem);
        usagecount = $('<div />').addClass('btn-group usage-count').appendTo(elem);
        for (const tr of ['unlimited', 'morning', 'afternoon', 'today']) {
            $('<button />').data('timerange-scope', tr).appendTo(timeranges);
        }
        for (const uc of [null, 1]) {
            $('<button />').data('usage-count', uc).appendTo(usagecount);
        }
        original_ts_request = ts.http_request;
    });
    hooks.afterEach(() => {
        ts.http_request = original_ts_request;
        elem.empty().remove();
        elem = null;
    });

    QUnit.test('initialize', (assert) => {
        ts.http_request = (opts) => {
            assert.step(`${opts.url} ${opts.params.usage_count}`);
        };
        elem.data('token-settings', { base_url: 'https://tld.com' });

        Token.initialize(elem.parent());

        // usage count buttons are bound by the created Token instance
        $($('button', usagecount)[1]).trigger('click');
        assert.verifySteps(['https://tld.com/update_token 1']);
    });

    QUnit.test('constructor', (assert) => {
        const settings = { timeranges: {} };
        elem.data('token-settings', settings);
        const token = new Token(elem);
        assert.strictEqual(token.settings, settings);
    });

    QUnit.test('request_api', (assert) => {
        let force_success = false;
        let force_data_success = false;

        // patch ts.http_request and action
        const original_ts_request = ts.http_request;
        const original_ts_action = ts.ajax.action;
        const original_ts_error = ts.show_error;
        ts.http_request = (opts) => {
            if (force_success) {
                if (force_data_success) {
                    opts.success({ success: force_data_success });
                } else {
                    opts.success({
                        success: force_data_success,
                        message: 'ajax_fail',
                    });
                }
            } else {
                opts.error(null, null, '');
            }
        };
        ts.ajax.action = () => {
            assert.step('ajax_success');
        };
        ts.show_error = (err) => {
            assert.step(err);
        };

        // define settings
        const settings = {
            base_url: 'https://tld.com',
        };
        elem.data('token-settings', settings);
        const token = new Token(elem);
        assert.strictEqual(token.settings, settings);

        // ajax error
        token.request_api({
            valid_from: '',
            valid_to: '',
        });
        assert.verifySteps(['Failed to request JSON API: ']);

        // ajax success, not data success
        force_success = true;
        token.request_api({
            valid_from: '',
            valid_to: '',
        });
        assert.verifySteps(['ajax_fail']);

        // ajax success
        force_data_success = true;
        token.request_api({
            valid_from: '2022-12-10T08:00:00.585Z',
            valid_to: '2022-12-10T012:00:00.585Z',
        });
        assert.verifySteps(['ajax_success']);

        // reset ts ajax
        ts.http_request = original_ts_request;
        ts.ajax.action = original_ts_action;
        ts.show_error = original_ts_error;
    });

    QUnit.test('set_timerange', (assert) => {
        //keep for testing
        const OriginalDateConstructor = Date;

        // patch Date constructor
        window.Date = ((oldDate) => {
            function MockDate(...args) {
                if (args.length === 0) {
                    //override the zero argument constructor
                    return new oldDate(MockDate.now());
                }

                //else delegate to the original constructor
                return new oldDate(...args);
            }
            //copy all properties from the original date, this includes the prototype
            const propertyDescriptors = Object.getOwnPropertyDescriptors(oldDate);
            Object.defineProperties(MockDate, propertyDescriptors);

            //override Date.now
            MockDate.now = () => 1670705688585;

            return MockDate;
        })(Date);

        const settings = {
            timeranges: {
                morning: {
                    start: '08:00',
                    end: '12:00',
                },
                afternoon: {
                    start: '12:00',
                    end: '18:00',
                },
                today: {
                    start: '08:00',
                    end: '18:00',
                },
            },
        };
        elem.data('token-settings', settings);
        const token = new Token(elem);
        let from, to;

        // patch request_api
        token.request_api = (params) => {
            from = params.valid_from;
            to = params.valid_to;
            assert.step('request_api');
        };
        assert.strictEqual(token.settings, settings);

        // unlimited
        const unlimited_btn = $('button', timeranges)[0];
        $(unlimited_btn).trigger('click');
        assert.verifySteps(['request_api']);
        assert.strictEqual(from, '');
        assert.strictEqual(to, '');
        // morning
        const morning_btn = $('button', timeranges)[1];
        $(morning_btn).trigger('click');
        assert.verifySteps(['request_api']);
        assert.strictEqual(from.slice(0, -5), '2022-12-10T08:00:00');
        assert.strictEqual(to.slice(0, -5), '2022-12-10T12:00:00');
        // afternoon
        const afternoon_btn = $('button', timeranges)[2];
        $(afternoon_btn).trigger('click');
        assert.verifySteps(['request_api']);
        assert.strictEqual(from.slice(0, -5), '2022-12-10T12:00:00');
        assert.strictEqual(to.slice(0, -5), '2022-12-10T18:00:00');
        // today
        const today_btn = $('button', timeranges)[3];
        $(today_btn).trigger('click');
        assert.verifySteps(['request_api']);
        assert.strictEqual(from.slice(0, -5), '2022-12-10T08:00:00');
        assert.strictEqual(to.slice(0, -5), '2022-12-10T18:00:00');

        // reset Date patch
        window.Date = OriginalDateConstructor;
    });

    QUnit.test('set_usage_count', (assert) => {
        const token = new Token(elem);
        // patch request_api
        token.request_api = (params) => {
            assert.step(`request_api ${params.usage_count}`);
        };
        // unlimited
        const unlimited_btn = $('button', usagecount)[0];
        $(unlimited_btn).trigger('click');
        assert.verifySteps(['request_api null']);
        // 1
        const one_btn = $('button', usagecount)[1];
        $(one_btn).trigger('click');
        assert.verifySteps(['request_api 1']);
    });
});
