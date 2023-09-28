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
import {Token} from '../src/token.js';
import ts from 'treibstoff';

QUnit.module('Token', hooks => {
    let elem,
        timeranges,
        usagecount;

    hooks.beforeEach(() => {
        elem = $('<div />')
            .addClass('token')
            .appendTo('body');
        timeranges = $('<div />')
            .addClass('btn-group timeranges')
            .appendTo(elem);
        usagecount = $('<div />')
            .addClass('btn-group usage-count')
            .appendTo(elem);
        for (let tr of ['unlimited', 'morning', 'afternoon', 'today']) {
            let btn = $('<button />')
                .data('timerange-scope', tr)
                .appendTo(timeranges);
        }
        for (let uc of [null, 1]) {
            let btn = $('<button />')
                .data('usage-count', uc)
                .appendTo(usagecount);
        }
    });
    hooks.afterEach(() => {
        elem.empty().remove();
        elem = null;
    });

    QUnit.test('constructor', assert => {
        let settings = {timeranges: {}};
        elem.data('token-settings', settings);
        let token = new Token(elem);
        assert.strictEqual(token.settings, settings);
    });

    QUnit.test('request_api', assert => {
        let force_success = false;
        let force_data_success = false;

        // patch ts.ajax.request and action
        const original_ts_request = ts.ajax.request;
        const original_ts_action = ts.ajax.action;
        const original_ts_error = ts.show_error;
        ts.ajax.request = function(opts) {
            if (force_success) {
                if (force_data_success) {
                    opts.success({success: force_data_success});
                } else {
                    opts.success({
                        success: force_data_success,
                        message: 'ajax_fail'
                    });
                }
            } else {
                opts.error(null, null, '');
            }
        }
        ts.ajax.action = function(opts) {
            assert.step('ajax_success');
        }
        ts.show_error = function(err) {
            assert.step(err);
        }

        // define settings
        let settings = {
            base_url: 'https://tld.com'
        };
        elem.data('token-settings', settings);
        let token = new Token(elem);
        assert.strictEqual(token.settings, settings);

        // ajax error
        token.request_api({
            valid_from: '',
            valid_to: ''
        });
        assert.verifySteps(['Failed to request JSON API: ']);

        // ajax success, not data success
        force_success = true;
        token.request_api({
            valid_from: '',
            valid_to: ''
        });
        assert.verifySteps(['ajax_fail']);

        // ajax success
        force_data_success = true;
        token.request_api({
            valid_from: '2022-12-10T08:00:00.585Z',
            valid_to: '2022-12-10T012:00:00.585Z'
        });
        assert.verifySteps(['ajax_success']);

        // reset ts ajax
        ts.ajax.request = original_ts_request;
        ts.ajax.action = original_ts_action;
        ts.show_error = original_ts_error;
    });

    QUnit.test('set_timerange', assert => {
        //keep for testing
        const OriginalDateConstructor = Date;

        // patch Date constructor
        Date = (function(oldDate) {
            function Date(...args) {
                if (args.length === 0) {
                //override the zero argument constructor
                return new oldDate(Date.now())
                } 
                
                //else delegate to the original constructor
                return new oldDate(...args);
            }
            //copy all properties from the original date, this includes the prototype
            const propertyDescriptors = Object.getOwnPropertyDescriptors(oldDate);
            Object.defineProperties(Date, propertyDescriptors);

            //override Date.now
            Date.now = function() {
                return 1670705688585;
            };

            return Date;
        })(Date);

        let settings = {
            timeranges: {
                "morning": {
                    "start": '08:00',
                    "end": '12:00'
                },
                "afternoon": {
                    "start": '12:00',
                    "end": '18:00'
                },
                "today": {
                    "start": '08:00',
                    "end": '18:00'
                }
            }
        };
        elem.data('token-settings', settings);
        let token = new Token(elem);
        let from, to;

        // patch request_api
        token.request_api = (params) => {
            from = params.valid_from;
            to = params.valid_to;
            assert.step('request_api');
        }
        assert.strictEqual(token.settings, settings);

        // unlimited
        let unlimited_btn = $('button', timeranges)[0];
        $(unlimited_btn).trigger('click');
        assert.verifySteps(['request_api']);
        assert.strictEqual(from, '');
        assert.strictEqual(to, '');
        // morning
        let morning_btn = $('button', timeranges)[1];
        $(morning_btn).trigger('click');
        assert.verifySteps(['request_api']);
        assert.strictEqual(from.slice(0, -5), '2022-12-10T08:00:00');
        assert.strictEqual(to.slice(0, -5), '2022-12-10T12:00:00');
        // afternoon
        let afternoon_btn = $('button', timeranges)[2];
        $(afternoon_btn).trigger('click');
        assert.verifySteps(['request_api']);
        assert.strictEqual(from.slice(0, -5), '2022-12-10T12:00:00');
        assert.strictEqual(to.slice(0, -5), '2022-12-10T18:00:00');
        // today
        let today_btn = $('button', timeranges)[3];
        $(today_btn).trigger('click');
        assert.verifySteps(['request_api']);
        assert.strictEqual(from.slice(0, -5), '2022-12-10T08:00:00');
        assert.strictEqual(to.slice(0, -5), '2022-12-10T18:00:00');

        // reset Date patch
        Date = OriginalDateConstructor;
    });

    QUnit.test('set_usage_count', assert => {
        let token = new Token(elem);
        // patch request_api
        token.request_api = (params) => {
            assert.step('request_api ' + params.usage_count);
        }
        // unlimited
        let unlimited_btn = $('button', usagecount)[0];
        $(unlimited_btn).trigger('click');
        assert.verifySteps(['request_api null']);
        // 1
        let one_btn = $('button', usagecount)[1];
        $(one_btn).trigger('click');
        assert.verifySteps(['request_api 1']);
    });
});
