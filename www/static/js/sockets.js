function logData(event) {
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
class CC {
    constructor(canvas) {
        this.URL = `${location.protocol}//${document.domain}:${location.port}`;
        this.canvas = canvas;
    }
    connect(callback) {
        var first = true;
        this.socket = io.connect(this.URL, {
            reconnection: false,
            timeout: 100 * 1000,
        });
        this.socket.on('connect', () => {
            this.registerSocketQueueEvents();
            this.registerSocketProcessEvents();
            this.registerSocketTestEvents();
            this.registerSocketDebugEvents();
            if (callback && first) {
                callback();
                first = false;
            }
        });
    }
    submitSolution(courseID, problemID, languageID, sourceCode, actionType, useDocker, on_complete, on_error) {
        this.on_complete = on_complete;
        this.on_error = on_error;
        this.socket.emit('student-solution-submit', {
            type: actionType,
            course: courseID,
            prob: problemID,
            lang: languageID,
            src: sourceCode,
            docker: useDocker,
        });
    }
    processSolution(_id, on_complete, on_error) {
        this.on_complete = on_complete;
        this.on_error = on_error;
        console.log('emitting process solution');
        this.socket.emit('student-process-solution', {
            _id: _id,
        });
    }
    drawTest(test) {
        var canvas = this.canvas.find(`#e-${test.uuid} .execution-test`);
        canvas.attr('class', `execution-test ${test.status}`);
        canvas.find('.test-title').html(Templates.render('test-title', test));
        canvas.find('.test-details').html(Templates.render('test-details', test));
        canvas.find('.cell-attachments').show().html(Templates.render('test-attachments', test));
        canvas.find('.cell-score').show().html(Templates.render('test-score', test));
        canvas.find('[data-toggle="tooltip"]').tooltip();
    }
    registerSocketDebugEvents() {
        this.socket.on('connect_timeout', () => {
            console.log('connect_timeout');
        });
        this.socket.on('connect_error', () => {
            console.log('connect_error');
        });
        this.socket.on('reconnect', (attemptNumber) => {
            console.log('reconnect ' + attemptNumber);
        });
        this.socket.on('reconnecting', (attemptNumber) => {
            console.log('reconnecting ' + attemptNumber);
        });
        this.socket.on('disconnect', (reason) => {
            if (reason === 'io server disconnect') {
                this.socket.connect();
            }
        });
        this.socket.on('debug', (event) => {
        });
    }
    registerSocketQueueEvents() {
        this.socket.on('queue-status', (event) => {
            this.canvas.html(Templates.render('queue/list-queue-items', event.data));
        });
        this.socket.on('queue-push', (event) => {
            logData(event);
            this.canvas.find('.queue-status ul').append(Templates.render('queue/list-queue-item', event.data));
            var item = document.getElementById('queue-' + event.data.id);
            $(item).css('display', 'none').show('fast');
        });
        this.socket.on('queue-pop', (event) => {
            var item = document.getElementById('queue-' + event.data.id);
            $(item).hide();
        });
    }
    registerSocketProcessEvents() {
        this.socket.on('process-start-me', (event) => {
            logData(event);
            this.canvas.html(Templates.render('process-execute', event));
            var nodes = "";
            event.data.results.forEach((item) => {
                nodes += Templates.render('test-result2', item);
            });
            this.canvas.find('.test-cases').html(nodes);
            this.canvas.find('.final-evaluation').html(Templates.render('test-result2', event.data.result));
        });
        this.socket.on('process-end-me', (event) => {
            logData(event);
            this.canvas.find('.evaluation').addClass(event.data.result.status).show().find('.evaluation-result').html(Templates.render('test-result2', event.data.result));
            this.drawTest(event.data.result);
            event.data.results.forEach((item) => {
                this.drawTest(item);
            });
            if (this.on_complete) {
                this.on_complete(event);
            }
        });
        this.socket.on('fatal-error', (event) => {
            logData(event);
            this.canvas.html(Templates.render('fatal-error', event));
            if (this.on_error) {
                this.on_error(event);
            }
        });
    }
    registerSocketTestEvents() {
        this.socket.on('execute-test-start-me', (event) => {
            logData(event);
            this.drawTest(event.data);
        });
        this.socket.on('execute-test-end-me', (event) => {
            logData(event);
            this.drawTest(event.data);
        });
        this.socket.on('compile-start-me', (event) => {
            logData(event);
            this.drawTest(event.data);
        });
        this.socket.on('compile-end-me', (event) => {
            logData(event);
            this.drawTest(event.data);
        });
    }
}
//# sourceMappingURL=sockets.js.map