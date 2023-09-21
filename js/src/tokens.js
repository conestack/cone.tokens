export class Tokens {

    static initialize(context) {
        $('.tokens-container', context).each(function() {
            new Tokens($(this));
        });
    }

    constructor(elem) {
        this.elem = elem;
        console.log(this);
    }
}
