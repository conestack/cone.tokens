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
process.env.CHROME_BIN = '/usr/bin/chromium';

// karma config
module.exports = function(config) {
    config.set({
        basePath: 'karma',
        frameworks: [
            'qunit'
        ],
        files: [
            {
            pattern: '../../node_modules/jquery/src/**/*.js',
            type: 'module',
            included: false
        }, 
        {
            pattern: `../../sources/treibstoff/src/*.js`,
            type: 'module',
            included: false
        }, {
            pattern: '../src/*.js',
            type: 'module',
            included: false
        }, {
            pattern: '../tests/test_*.js',
            type: 'module'
        }],
        browsers: [
            'ChromeHeadless'
        ],
        singleRun: true,
        reporters: [
            'progress',
            'coverage'
        ],
        preprocessors: {
            '../src/*.js': [
                'coverage',
                'module-resolver'
            ],
            '../tests/*.js': [
                'coverage',
                'module-resolver'
            ],
            '../../sources/treibstoff/src/*.js': [
                'module-resolver'
            ]
        },
        moduleResolverPreprocessor: {
            addExtension: null,
            customResolver: null,
            ecmaVersion: 6,
            aliases: {
                jquery: '../../node_modules/jquery/src/jquery.js',
                treibstoff: '../../sources/treibstoff/src/treibstoff.js',
            }
        }
    });
};
