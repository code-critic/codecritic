class Globals {
    static initEnv() {
        var URL = `${location.protocol}//${document.domain}:${location.port}`;
        this.env = nunjucks.configure(URL, {
            autoescape: true,
        });
        this.env.addFilter('toFixed', (num, digits) => {
            return parseFloat(num).toFixed(digits || 2);
        });
        this.env.addFilter('pad', (n, w = 2, z = '0') => {
            let m = n.toString();
            return m.length >= w ? m : new Array(w - m.length + 1).join(z) + m;
        });
        this.env.addFilter('cut', (str, digits) => {
            return str.substring(0, digits || 8);
        });
        this.env.addGlobal('inArray', function (value, arr) {
            return arr.includes(value);
        });
        this.env.addFilter('toFixed', function (num, digits) {
            return parseFloat(num).toFixed(digits);
        });
        window.toastr.options.progressBar = true;
    }
}
class Templates {
    static render(template, data) {
        var templateUrl = `static/templates/${template}.njk`;
        var njk = this.templates[template];
        if (njk) {
            return njk.render(data);
        }
        else {
            this.templates[template] = Globals.env.getTemplate(templateUrl, true);
            return this.templates[template].render(data);
        }
    }
}
Templates.templates = {};
//# sourceMappingURL=templates.js.map