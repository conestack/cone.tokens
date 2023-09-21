import cleanup from 'rollup-plugin-cleanup';
import terser from '@rollup/plugin-terser';

const out_dir = 'src/cone/tokens/browser/static';

export default args => {
    let conf = {
        input: 'js/src/bundle.js',
        plugins: [
            cleanup()
        ],
        output: [{
            name: 'cone_tokens',
            file: `${out_dir}/cone.tokens.js`,
            format: 'iife',
            globals: {
                jquery: 'jQuery',
                treibstoff: 'ts'
            },
            interop: 'default',
            sourcemap: false
        }],
        external: [
            'jquery',
            'treibstoff'
        ]
    };
    if (args.configDebug !== true) {
        conf.output.push({
            name: 'cone_tokens',
            file: `${out_dir}/cone.tokens.min.js`,
            format: 'iife',
            plugins: [
                terser()
            ],
            globals: {
                jquery: 'jQuery',
                treibstoff: 'ts'
            },
            interop: 'default',
            sourcemap: false
        });
    }
    return conf;
};
