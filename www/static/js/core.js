var Automatest = (function() {

  var namespace = '';
  var root = '';
  var $target = '';
  var callback = null;
  var URL = location.protocol + '//' + document.domain + ':' + location.port + namespace;
  // https://socket.io/docs/client-api/
  var socket = io.connect(URL, {
    timeout: 100 * 1000,
  });
  var env = nunjucks.configure(URL, {
    autoescape: true
  });
  env.addGlobal('inArray', function(value, arr) {
    return arr.includes(value);
  });
  env.addFilter('toFixed', function(num, digits) {
    return parseFloat(num).toFixed(digits)
  });

  socket.on('connect', function() {
    console.log('connected');
  });
  socket.on('connect_timeout', function() {
    console.log('connect_timeout');
  });
  socket.on('connect_error', function() {
    console.log('connect_error');
  });

  socket.on('reconnect', (attemptNumber) => {
    console.log('reconnect' + attemptNumber);
  });
  socket.on('reconnecting', (attemptNumber) => {
    console.log('reconnecting' + attemptNumber);
  });
  socket.on('disconnect', (reason) => {
    console.log('disconnect');
    console.log(reason);
    if (reason === 'io server disconnect') {
      // the disconnection was initiated by the server, you need to reconnect manually
      socket.connect();
    }
    // else the socket will automatically try to reconnect
  });

  var oldOnevent = socket.onevent;
  socket.onevent = function(packet) {
    if (packet.data) {
      console.log('>>>', {
        name: packet.data[0],
        payload: packet.data[1]
      })
    }
    oldOnevent.apply(socket, arguments)
  }

  socket.on('debug', function(event) {
    logData(event);
  });

  socket.on('queue-status', function(event) {
    $target.html(
      nunjucks.render(root + 'static/templates/list-queue-items.njk', event.data)
    );
  });

  socket.on('queue-push', function(event) {
    logData(event);

    $target.find('.queue-status ul').append(
      nunjucks.render(root + 'static/templates/list-queue-item.njk', event.data)
    );
    var item = document.getElementById('queue-' + event.data.id);
    $(item).css('display', 'none').show('fast');
  });

  socket.on('queue-pop', function(event) {
    logData(event);

    var item = document.getElementById('queue-' + event.data.id);
    $(item).hide();
  });

  socket.on('process-start-me', function(event) {
    logData(event);
    
    $target.html(
      nunjucks.render(root + 'static/templates/process-execute.njk', event)
    );
    // for (id in event.results) {
    //   var item = event.results[id];
    //   $('#e-' + item.uuid).html(
    //     nunjucks.render(root + 'static/templates/test-result.njk', item)
    //   )
    // }
    $('.execution > .execution-entry').hide().show('fast');
  });

  socket.on('process-end-me', function(event) {
    logData(event);
    
    $target.find('.evaluation').show().find('.evaluation-result').html(
      nunjucks.render(root + 'static/templates/test-result.njk', event.data.evaluation)
    )
    $target.find('.answer-correct,.ok').find('.collapse').addClass('show');
    $target.find('.collapse').collapse();
    if (callback) {
      callback(event);
    }
  });

  socket.on('execute-test-start-me', function(event) {
    logData(event);
    
    $('#e-' + event.test.uuid).html(
      nunjucks.render(root + 'static/templates/test-result.njk', event.test)
    );
  });

  socket.on('execute-test-end-me', function(event) {
    logData(event);
    
    console.log(event);
    $('#e-' + event.test.uuid).html(
      nunjucks.render(root + 'static/templates/test-result.njk', event.test)
    );
  });

  socket.on('fatal-error', function(event) {
    logData(event);
    $target.html(
      nunjucks.render(root + 'static/templates/fatal-error.njk', event)
    );

    if (callback) {
      callback(event);
    }
  });

  socket.on('compile-start-me', function(event) {
    logData(event);
    $target.find('.compilation').html(
      nunjucks.render(root + 'static/templates/test-result.njk', event.result)
    )
  });
  socket.on('compile-end-me', function(event) {
    logData(event);
    $target.find('.compilation').html(
      nunjucks.render(root + 'static/templates/test-result.njk', event.result)
    )
  });

  return {
    socket: socket,
    setTarget(target) {
      $target = $(target);
    },
    submitSolution: function(courseID, problemID, languageID, sourceCode, actionType, useDocker, _callback) {
      callback = _callback;
      socket.emit('student-solution-submit', {
        type: actionType,
        course: courseID,
        prob: problemID,
        lang: languageID,
        src: sourceCode,
        docker: useDocker,
      });
    },
  }
})();

var toArray = function(arr) {
  return Array.isArray(arr) ? arr : [arr];
}

var storagePut = function(idx, value) {
  var key = toArray(idx).join('/');
  try {
    localStorage.setItem(key, value);
  } catch (e) {
    // ignore local storage error
  }
};

var storageGet = function(idx, def) {
  var key = toArray(idx).join('/');
  try {
    if (key in localStorage) {
      return localStorage.getItem(key);
    } else {
      return def === undefined ? null : def;
    }
  } catch (e) {
    // ignore local storage error
    return def === undefined ? null : def;
  }
};


var courseStorage = function(courseID) {
  var course = toArray(courseID);

  return {
    storageGet: function(idx, def) {
      return storageGet(course.concat(toArray(idx)), def);
    },
    storagePut: function(idx, value) {
      return storagePut(course.concat(toArray(idx)), value);
    }
  }
};

var registerDnD = function(holder, success) {
  if (!window.FileReader) {
    return false;
  }
  
  // max size of 2 MB
  var MAX_SIZE = 1024 * 1024 * 2;
  var $holder = $(holder);
  $holder.addClass('draggable');
  holder = $holder.get(0);

  holder.ondragover = function(e) {
    e.preventDefault();
    e.stopPropagation();
    $holder.addClass('hover');
    return false;
  };
  holder.ondragenter = function(e) {
    e.preventDefault();
    e.stopPropagation();
    $holder.addClass('hover');
    return false;
  };

  holder.ondragleave = function(e) {
    e.preventDefault();
    e.stopPropagation();
    $holder.removeClass('hover');
    return false;
  };
  holder.ondragend = function(e) {
    e.preventDefault();
    e.stopPropagation();
    $holder.removeClass('hover');
    return false;
  };

  holder.ondrop = function(e) {
    e.preventDefault();
    e.stopPropagation();
    $holder.removeClass('hover');

    try {
      var file = e.dataTransfer.files[0];
      var reader = new FileReader();
      if (file.size > MAX_SIZE) {
        alert('The file is too big');
        return false;
      }

      reader.onload = function(event) {
        success(file, event.target.result);
      };

      reader.readAsText(file);
    } catch (e) {
      console.log(e);
    }


    return false;
  };
};



var logData = function(data) {
  if (data.data == 'ok, connected') {
    $('#log').empty();
  }
  var copy = $.extend(true, {}, data);
  var msg = '<b>' + copy.event + '</b>: ';
  delete copy.event;
  delete copy.status;
  msg += JSON.stringify(copy) + '\n';
  $('#log').append(msg);
};

var _showcase = {
  "results": {
    IN_QUEUE: {
      "cmd": [],
      "console": [],
      "duration": 0,
      "id": "ExecutorStatus.IN_QUEUE",
      "message": "ExecutorStatus.IN_QUEUE",
      "message_details": [],
      "returncode": null,
      "status": "in-queue",
      "stderr": [],
      "stdin": [],
      "stdout": [],
      "uuid": "d5f2588bb2e9b63063eb4d5db43c13c01bd96866"
    },
    RUNNING: {
      "cmd": [],
      "console": [],
      "duration": 0,
      "id": "ExecutorStatus.RUNNING",
      "message": "ExecutorStatus.RUNNING",
      "message_details": [],
      "returncode": null,
      "status": "running",
      "stderr": [],
      "stdin": [],
      "stdout": [],
      "uuid": "a216200b0e7fac3296fbef0c06df1367d872b840"
    },
    IGNORE: {
      "cmd": [],
      "console": [],
      "duration": 0,
      "id": "ExecutorStatus.IGNORE",
      "message": "ExecutorStatus.IGNORE",
      "message_details": [],
      "returncode": null,
      "status": "ignore",
      "stderr": [],
      "stdin": [],
      "stdout": [],
      "uuid": "b5b18180580381272bacd032d5a51e96c86dd586"
    },
    OK: {
      "cmd": [],
      "console": [],
      "duration": 0,
      "id": "ExecutorStatus.OK",
      "message": "ExecutorStatus.OK",
      "message_details": [],
      "returncode": null,
      "status": "ok",
      "stderr": [],
      "stdin": [],
      "stdout": [],
      "uuid": "46c48c19ddd8ab3df6f48fd4cd8ac522f659cbac"
    },
    ANSWER_CORRECT: {
      "cmd": [],
      "console": [],
      "duration": 0,
      "id": "ExecutorStatus.ANSWER_CORRECT",
      "message": "ExecutorStatus.ANSWER_CORRECT",
      "message_details": [],
      "returncode": null,
      "status": "answer-correct",
      "stderr": [],
      "stdin": [],
      "stdout": [],
      "uuid": "a7b113d80fa9e2edccd52a52fffd2d5a24b5aea7"
    },
    ANSWER_CORRECT_TIMEOUT: {
      "cmd": [],
      "console": [],
      "duration": 0,
      "id": "ExecutorStatus.ANSWER_CORRECT_TIMEOUT",
      "message": "ExecutorStatus.ANSWER_CORRECT_TIMEOUT",
      "message_details": [],
      "returncode": null,
      "status": "answer-correct-timeout",
      "stderr": [],
      "stdin": [],
      "stdout": [],
      "uuid": "88aeb82278cdf663a52b7a73c885d66f6633b53b"
    },
    ANSWER_WRONG: {
      "cmd": [],
      "console": [],
      "duration": 0,
      "id": "ExecutorStatus.ANSWER_WRONG",
      "message": "ExecutorStatus.ANSWER_WRONG",
      "message_details": [],
      "returncode": null,
      "status": "answer-wrong",
      "stderr": [],
      "stdin": [],
      "stdout": [],
      "uuid": "8434f46886c76fbd29fee76bd3e136e497de59b5"
    },
    ANSWER_WRONG_TIMEOUT: {
      "cmd": [],
      "console": [],
      "duration": 0,
      "id": "ExecutorStatus.ANSWER_WRONG_TIMEOUT",
      "message": "ExecutorStatus.ANSWER_WRONG_TIMEOUT",
      "message_details": [],
      "returncode": null,
      "status": "answer-wrong-timeout",
      "stderr": [],
      "stdin": [],
      "stdout": [],
      "uuid": "4ba7e3ef76bc013869e7df456f2b1c3206aa2e2a"
    },
    SKIPPED: {
      "cmd": [],
      "console": [],
      "duration": 0,
      "id": "ExecutorStatus.SKIPPED",
      "message": "ExecutorStatus.SKIPPED",
      "message_details": [],
      "returncode": null,
      "status": "skipped",
      "stderr": [],
      "stdin": [],
      "stdout": [],
      "uuid": "491d1f548ccc7d028e8de8f92eb61c41454dc1e4"
    },
    SOFT_TIMEOUT: {
      "cmd": [],
      "console": [],
      "duration": 0,
      "id": "ExecutorStatus.SOFT_TIMEOUT",
      "message": "ExecutorStatus.SOFT_TIMEOUT",
      "message_details": [],
      "returncode": null,
      "status": "soft-timeout",
      "stderr": [],
      "stdin": [],
      "stdout": [],
      "uuid": "10fa7e263c084952f5385dc618059c3e64aefd06"
    },
    GLOBAL_TIMEOUT: {
      "cmd": [],
      "console": [],
      "duration": 0,
      "id": "ExecutorStatus.GLOBAL_TIMEOUT",
      "message": "ExecutorStatus.GLOBAL_TIMEOUT",
      "message_details": [],
      "returncode": null,
      "status": "global-timeout",
      "stderr": [],
      "stdin": [],
      "stdout": [],
      "uuid": "483a78795ca564cd1c30f5e72c9fc00c46c40d0b"
    },
    FILE_NOT_FOUND: {
      "cmd": [],
      "console": [],
      "duration": 0,
      "id": "ExecutorStatus.FILE_NOT_FOUND",
      "message": "ExecutorStatus.FILE_NOT_FOUND",
      "message_details": [],
      "returncode": null,
      "status": "file-not-found",
      "stderr": [],
      "stdin": [],
      "stdout": [],
      "uuid": "624581e2c9affd98b09ec0e5aac308d4454373be"
    },
    ERROR_WHILE_RUNNING: {
      "cmd": [],
      "console": [],
      "duration": 0,
      "id": "ExecutorStatus.ERROR_WHILE_RUNNING",
      "message": "ExecutorStatus.ERROR_WHILE_RUNNING",
      "message_details": [],
      "returncode": null,
      "status": "error-while-running",
      "stderr": [],
      "stdin": [],
      "stdout": [],
      "uuid": "c1b07a5a8ad543916cbe39ec2d9fe234d0bff1b2"
    }
  },
  "user": "jan.hybs",
  "uuid": "fbf00cd60a3c4419b6410d3145253019"
};

$(document).ready(function() {
  $('[data-toggle="tooltip"]').tooltip();
});
