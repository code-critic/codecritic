function logData(event) {
    console.log(event);
}
var Status;
(function (Status) {
    Status["IN_QUEUE"] = "in-queue";
    Status["RUNNING"] = "running";
    Status["IGNORE"] = "ignore";
    Status["OK"] = "ok";
    Status["ANSWER_CORRECT"] = "answer-correct";
    Status["ANSWER_CORRECT_TIMEOUT"] = "answer-correct-timeout";
    Status["ANSWER_WRONG"] = "answer-wrong";
    Status["ANSWER_WRONG_TIMEOUT"] = "answer-wrong-timeout";
    Status["SKIPPED"] = "skipped";
    Status["SOFT_TIMEOUT"] = "soft-timeout";
    Status["GLOBAL_TIMEOUT"] = "global-timeout";
    Status["FILE_NOT_FOUND"] = "file-not-found";
    Status["ERROR_WHILE_RUNNING"] = "error-while-running";
    Status["COMPILATION_FAILED"] = "compilation-failed";
})(Status || (Status = {}));
var CC = (function () {
    function CC(canvas) {
        this.URL = location.protocol + "//" + document.domain + ":" + location.port;
        this.canvas = canvas;
    }
    CC.prototype.connect = function (callback) {
        var _this = this;
        var first = true;
        this.socket = io.connect(this.URL, {
            reconnection: false,
            timeout: 100 * 1000
        });
        this.socket.on('connect', function () {
            _this.registerSocketQueueEvents();
            _this.registerSocketProcessEvents();
            _this.registerSocketTestEvents();
            _this.registerSocketDebugEvents();
            if (callback && first) {
                callback();
                first = false;
            }
        });
    };
    CC.prototype.submitSolution = function (courseID, problemID, languageID, sourceCode, actionType, useDocker, on_complete, on_error) {
        this.on_complete = on_complete;
        this.on_error = on_error;
        this.socket.emit('student-solution-submit', {
            type: actionType,
            course: courseID,
            prob: problemID,
            lang: languageID,
            src: sourceCode,
            docker: useDocker
        });
    };
    CC.prototype.processSolution = function (uuid, on_complete, on_error) {
        this.on_complete = on_complete;
        this.on_error = on_error;
        console.log('emitting process solution');
        this.socket.emit('student-process-solution', {
            uuid: uuid
        });
    };
    CC.prototype.drawTest = function (test) {
        var canvas = this.canvas.find("#e-" + test.uuid + " .execution-test");
        canvas.attr('class', "execution-test " + test.status);
        canvas.find('.test-title').html(Templates.testTitle.render(test));
        canvas.find('.test-details').html(Templates.testDetails.render(test));
        canvas.find('.cell-attachments').show().html(Templates.testAttachments.render(test));
        canvas.find('.cell-score').show().html(Templates.testScore.render(test));
        canvas.find('[data-toggle="tooltip"]').tooltip();
    };
    CC.prototype.registerSocketDebugEvents = function () {
        var _this = this;
        this.socket.on('connect_timeout', function () {
            console.log('connect_timeout');
        });
        this.socket.on('connect_error', function () {
            console.log('connect_error');
        });
        this.socket.on('reconnect', function (attemptNumber) {
            console.log('reconnect ' + attemptNumber);
        });
        this.socket.on('reconnecting', function (attemptNumber) {
            console.log('reconnecting ' + attemptNumber);
        });
        this.socket.on('disconnect', function (reason) {
            console.log('disconnect', reason);
            if (reason === 'io server disconnect') {
                _this.socket.connect();
            }
        });
        this.socket.on('debug', function (event) {
            console.log(event);
        });
    };
    CC.prototype.registerSocketQueueEvents = function () {
        var _this = this;
        this.socket.on('queue-status', function (event) {
            _this.canvas.html(Templates.listQueueItems.render(event.data));
        });
        this.socket.on('queue-push', function (event) {
            logData(event);
            _this.canvas.find('.queue-status ul').append(Templates.listQueueItem.render(event.data));
            var item = document.getElementById('queue-' + event.data.id);
            $(item).css('display', 'none').show('fast');
        });
        this.socket.on('queue-pop', function (event) {
            var item = document.getElementById('queue-' + event.data.id);
            $(item).hide();
        });
    };
    CC.prototype.registerSocketProcessEvents = function () {
        var _this = this;
        this.socket.on('process-start-me', function (event) {
            logData(event);
            _this.canvas.html(Templates.processExecute.render(event));
            var nodes = "";
            event.data.results.forEach(function (item) {
                nodes += Templates.testResult2.render(item);
            });
            _this.canvas.find('.test-cases').html(nodes);
            _this.canvas.find('.final-evaluation').html(Templates.testResult2.render(event.data.result));
        });
        this.socket.on('process-end-me', function (event) {
            logData(event);
            _this.canvas.find('.evaluation').addClass(event.data.result.status).show().find('.evaluation-result').html(Templates.testResult2.render(event.data.result));
            _this.drawTest(event.data.result);
            event.data.results.forEach(function (item) {
                _this.drawTest(item);
            });
            if (_this.on_complete) {
                _this.on_complete(event);
            }
        });
        this.socket.on('fatal-error', function (event) {
            logData(event);
            _this.canvas.html(Templates.fatalError.render(event));
            if (_this.on_error) {
                _this.on_error(event);
            }
        });
    };
    CC.prototype.registerSocketTestEvents = function () {
        var _this = this;
        this.socket.on('execute-test-start-me', function (event) {
            logData(event);
            _this.drawTest(event.data);
        });
        this.socket.on('execute-test-end-me', function (event) {
            logData(event);
            _this.drawTest(event.data);
        });
        this.socket.on('compile-start-me', function (event) {
            logData(event);
            _this.drawTest(event.data);
        });
        this.socket.on('compile-end-me', function (event) {
            logData(event);
            _this.drawTest(event.data);
        });
    };
    return CC;
}());
