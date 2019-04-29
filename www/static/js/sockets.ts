/// <reference path="/home/jan-hybs/typings/globals/socket.io/socket.io-client.d.ts"/>
/// <reference path="/home/jan-hybs/typings/globals/nunjucks/nunjucks.d.ts"/>
/// <reference path="/home/jan-hybs/typings/globals/jquery/index.d.ts"/>
/// <reference path="templates.ts"/>

function logData(event) {
  console.log(event);
}

enum Status {
  IN_QUEUE = "in-queue",
  RUNNING = "running",
  IGNORE = "ignore",
  OK = "ok",
  ANSWER_CORRECT = "answer-correct",
  ANSWER_CORRECT_TIMEOUT = "answer-correct-timeout",
  ANSWER_WRONG = "answer-wrong",
  ANSWER_WRONG_TIMEOUT = "answer-wrong-timeout",
  SKIPPED = "skipped",
  SOFT_TIMEOUT = "soft-timeout",
  GLOBAL_TIMEOUT = "global-timeout",
  FILE_NOT_FOUND = "file-not-found",
  ERROR_WHILE_RUNNING = "error-while-running",
  COMPILATION_FAILED = "compilation-failed",
}

interface TestAttachment {
  name: string;
  path: string;
}

interface TestResult {
  id: string;
  uuid: string;
  status: Status;
  attachments: TestAttachment[];
  duration: number;

  scores: number[];
  score: number;
  returncode: number;

  console: string[];
  message: string;
  message_details: string[];
}

interface Problem {
    action: string;
    course: any;
    lang: any;
    user: any;
    uuid: string;
    result: TestResult;
    results: TestResult[];
}

interface TestEvent {
  data: TestResult;
}

interface ProblemEvent {
  data: Problem;
}

class CC {
  private socket: SocketIOClient.Socket;
  private canvas: JQuery;
  private URL: string = `${location.protocol}//${document.domain}:${location.port}`;
  public on_complete: Function;
  public on_error: Function;


  constructor(canvas: JQuery) {
    this.canvas = canvas;
  }

  public connect(callback?: Function) {
    var first: boolean = true;
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

  public submitSolution(
    courseID: string, problemID: string, languageID: string,
    sourceCode: string, actionType: string, useDocker: boolean,
    on_complete?: Function, on_error?: Function) {

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
  public processSolution(uuid: string, on_complete?: Function, on_error?: Function) {
    this.on_complete = on_complete;
    this.on_error = on_error;
    console.log('emitting process solution');
    this.socket.emit('student-process-solution', {
      uuid: uuid,
    });
  }

  private drawTest(test: TestResult) {
    var canvas: JQuery = this.canvas.find(`#e-${test.uuid} .execution-test`);
    canvas.attr('class', `execution-test ${test.status}`);

    canvas.find('.test-title').html(
      Templates.testTitle.render(test)
    );
    canvas.find('.test-details').html(
      Templates.testDetails.render(test)
    );
    canvas.find('.cell-attachments').show().html(
      Templates.testAttachments.render(test)
    );
    canvas.find('.cell-score').show().html(
      Templates.testScore.render(test)
    );
    canvas.find('[data-toggle="tooltip"]').tooltip();
  }

  private registerSocketDebugEvents() {
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
      console.log('disconnect', reason);
      if (reason === 'io server disconnect') {
        // the disconnection was initiated by the server, you need to reconnect manually
        this.socket.connect();
      }
    });
    this.socket.on('debug', (event) => {
      console.log(event);
    });
  }

  private registerSocketQueueEvents() {
    this.socket.on('queue-status', (event) => {
      this.canvas.html(
        Templates.listQueueItems.render(event.data)
      );
    });

    this.socket.on('queue-push', (event) => {
      logData(event);

      this.canvas.find('.queue-status ul').append(
        Templates.listQueueItem.render(event.data)
      );
      var item = document.getElementById('queue-' + event.data.id);
      $(item).css('display', 'none').show('fast');
    });

    this.socket.on('queue-pop', (event) => {
      var item = document.getElementById('queue-' + event.data.id);
      $(item).hide();
    });
  }

  private registerSocketProcessEvents() {
    this.socket.on('process-start-me', (event: ProblemEvent) => {
      logData(event);

      this.canvas.html(
        Templates.processExecute.render(event)
      );
      var nodes = "";
      event.data.results.forEach((item) => {
        nodes += Templates.testResult2.render(item)
      });
      this.canvas.find('.test-cases').html(nodes);
      this.canvas.find('.final-evaluation').html(
        Templates.testResult2.render(event.data.result)
      );
    });

    this.socket.on('process-end-me', (event: ProblemEvent) => {
      logData(event);
      this.canvas.find('.evaluation').addClass(event.data.result.status).show().find('.evaluation-result').html(
        Templates.testResult2.render(event.data.result)
      )
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
      this.canvas.html(
        Templates.fatalError.render(event)
      );
      if (this.on_error) {
        this.on_error(event);
      }
    });
  }

  private registerSocketTestEvents() {
    this.socket.on('execute-test-start-me', (event: TestEvent) => {
      logData(event);
      this.drawTest(event.data);
    });

    this.socket.on('execute-test-end-me', (event: TestEvent) => {
      logData(event);
      this.drawTest(event.data);
    });

    this.socket.on('compile-start-me', (event: TestEvent) => {
      logData(event);
      this.drawTest(event.data);
    });

    this.socket.on('compile-end-me', (event: TestEvent) => {
      logData(event);
      this.drawTest(event.data);
    });
  }
}
