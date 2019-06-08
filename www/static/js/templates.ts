/// <reference path="/home/jan-hybs/typings/globals/nunjucks/nunjucks.d.ts"/>

interface String {
    format(...args): string;
}

String.prototype.format = function() {
    var formatted = this;
    for (var i = 0; i < arguments.length; i++) {
        var regexp = new RegExp('\\{'+i+'\\}', 'gi');
        formatted = formatted.replace(regexp, arguments[i]);
    }
    return formatted;
};

class Globals {
  static env: nunjucks.Environment;

  static initEnv() {
    var URL = `${location.protocol}//${document.domain}:${location.port}`;
    this.env = nunjucks.configure(URL, {
      autoescape: true,
    });
    this.env.addFilter('toFixed', (num, digits) => {
      return parseFloat(num).toFixed(digits || 2)
    });
    this.env.addFilter('pad', (n: number, w: number = 2, z: string = '0') => {
      let m = n.toString();
      return m.length >= w ? m : new Array(w - m.length + 1).join(z) + m;
    });
    this.env.addFilter('cut', (str, digits) => {
      return str.substring(0, digits || 8)
    });
    this.env.addGlobal('inArray', function(value, arr) {
      return arr.includes(value);
    });
    this.env.addFilter('toFixed', function(num, digits) {
      return parseFloat(num).toFixed(digits)
    });

    (<any>window).toastr.options.progressBar = true;
    // (<any> window).toastr.options.timeOut = 30000;
    // (<any> window).toastr.options.extendedTimeOut = 30000;
  }
}

class Templates {
  // static listQueueItems: nunjucks.Template;
  // static listQueueItem: nunjucks.Template;
  // static processExecute: nunjucks.Template;
  // static testResult2: nunjucks.Template;
  // static fatalError: nunjucks.Template;
  // static testTitle: nunjucks.Template;
  // static testDetails: nunjucks.Template;
  // static testScore: nunjucks.Template;
  // static testAttachments: nunjucks.Template;
  // 
  // static reviewEditor: nunjucks.Template;
  // static reviewComment: nunjucks.Template;
  // 
  // static adminFilters: nunjucks.Template;
  // static adminUserResults: nunjucks.Template;
  private static templates: { [key: string]: nunjucks.Template } = {};
  
  // static loadTemplates() {
  //   var compileNow: boolean = true;
  //   this.listQueueItems = Globals.env.getTemplate("static/templates/list-queue-items.njk", compileNow);
  //   this.listQueueItem = Globals.env.getTemplate("static/templates/list-queue-item.njk", compileNow);
  //   this.processExecute = Globals.env.getTemplate("static/templates/process-execute.njk", compileNow);
  //   this.testResult2 = Globals.env.getTemplate("static/templates/test-result2.njk", compileNow);
  //   this.fatalError = Globals.env.getTemplate("static/templates/fatal-error.njk", compileNow);
  //   this.testTitle = Globals.env.getTemplate("static/templates/test-title.njk", compileNow);
  //   this.testDetails = Globals.env.getTemplate("static/templates/test-details.njk", compileNow);
  //   this.testScore = Globals.env.getTemplate("static/templates/test-score.njk", compileNow);
  //   this.testAttachments = Globals.env.getTemplate("static/templates/test-attachments.njk", compileNow);
  // 
  //   //this.notifications = Globals.env.getTemplate("static/templates/common/notifications.njk", compileNow);
  //   // this._notifications = null;
  // 
  //   this.reviewEditor = Globals.env.getTemplate("static/templates/review/review-editor.njk", compileNow);
  //   this.reviewComment = Globals.env.getTemplate("static/templates/review/review-comment.njk", compileNow);
  // 
  //   this.adminFilters = Globals.env.getTemplate("static/templates/admin/filters.njk", compileNow);
  //   this.adminUserResults = Globals.env.getTemplate("static/templates/admin/user-results.njk", compileNow);
  // }
  
  public static render(template: string, data: any): string {
    var templateUrl = `static/templates/${template}.njk`;
    var njk = this.templates[template];
    if (njk) {
        return njk.render(data);
    } else {
        this.templates[template] = Globals.env.getTemplate(templateUrl, true);
        return this.templates[template].render(data);
    }
  }
}





















//
