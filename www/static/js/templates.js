var Globals = (function () {
    function Globals() {
    }
    Globals.initEnv = function () {
        var URL = location.protocol + "//" + document.domain + ":" + location.port;
        this.env = nunjucks.configure(URL, {
            autoescape: true
        });
        this.env.addFilter('toFixed', function (num, digits) {
            return parseFloat(num).toFixed(digits || 2);
        });
        this.env.addFilter('pad', function (n, w, z) {
            if (w === void 0) { w = 2; }
            if (z === void 0) { z = '0'; }
            var m = n.toString();
            return m.length >= w ? m : new Array(w - m.length + 1).join(z) + m;
        });
        this.env.addFilter('cut', function (str, digits) {
            return str.substring(0, digits || 8);
        });
        this.env.addGlobal('inArray', function (value, arr) {
            return arr.includes(value);
        });
        this.env.addFilter('toFixed', function (num, digits) {
            return parseFloat(num).toFixed(digits);
        });
    };
    return Globals;
}());
var Templates = (function () {
    function Templates() {
    }
    Templates.loadTemplates = function () {
        var compileNow = true;
        this.listQueueItems = Globals.env.getTemplate("static/templates/list-queue-items.njk", compileNow);
        this.listQueueItem = Globals.env.getTemplate("static/templates/list-queue-item.njk", compileNow);
        this.processExecute = Globals.env.getTemplate("static/templates/process-execute.njk", compileNow);
        this.testResult2 = Globals.env.getTemplate("static/templates/test-result2.njk", compileNow);
        this.fatalError = Globals.env.getTemplate("static/templates/fatal-error.njk", compileNow);
        this.testTitle = Globals.env.getTemplate("static/templates/test-title.njk", compileNow);
        this.testDetails = Globals.env.getTemplate("static/templates/test-details.njk", compileNow);
        this.testScore = Globals.env.getTemplate("static/templates/test-score.njk", compileNow);
        this.testAttachments = Globals.env.getTemplate("static/templates/test-attachments.njk", compileNow);
    };
    return Templates;
}());
