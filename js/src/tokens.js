export class Tokens {

    static initialize(context) {
        $('.tokens-container', context).each(function() {
            new Tokens($(this));
        });
    }

    constructor(elem) {
        this.elem = elem;
        this.token_uid_elem = $('[name=token-uid]', elem);
        this.scan_token_elem = $('.scan-token', elem);

        this.scan_token = this.scan_token.bind(this);
        this.scan_token_elem.on('click', (e) => {
            this.scan_token();
        });
    }

    scan_token() {
        uid_elem = this.token_uid_elem;
        uid_elem.val('');
        uid_elem[0].focus();
        uid_elem.on('change', () => {
            console.log('change');
            let val = uid_elem.val();
            if (val.length == 36) {
                uid_elem.val('');
                uid_elem.off('change');
            };
        });
    }
}
