$(document).ready(function() {
  var previous = $('#solution-result-previous');
  var current = $('#solution-result-current');
  var sourceCode = $('#source-code');
  var requestReviewBtn = $('#request-review-btn');
  var sourceCodeBlock = $('#source-code').find('pre code').get(0);
  var _id = current.data('_id');

  var finished = false;
  var currentSrc = null;
  var lastObject = null;
  var lastTarget = null;

  var cc = new CC(current);
  var ccp = new CC(previous);

  var onRender = function() {
    if (lastObject.review_request_) {
      requestReviewBtn.fadeOut('fast');
    } else {
      requestReviewBtn.fadeIn('fast');
      requestReviewBtn.removeClass('disabled alpha-5');
    }
  };

  requestReviewBtn.click(function(ev) {
    $.ajax({
      type: 'POST',
      url: '/api/codereview/add',
      dataType: 'json',
      contentType: 'application/json;charset=UTF-8',
      data: JSON.stringify({
        _id: lastObject._id
      }),
      success: function(data) {
        if (data.result == 'ok') {
          window.toastr.success('Following teachers have been notified: ' + data.reviewers.join(','), 'Request sent');
          requestReviewBtn.fadeOut('fast');
        } else if (data.result == 'warning') {
          window.toastr.warning(data.message, 'Request already sent');
          requestReviewBtn.fadeOut('fast');
        }
      }
    });
    return false;
  });

  var submitSolution = function() {
    cc.processSolution(_id,
      function(event) {
        $('.live-result').addClass(event.data.result.status);
        finished = true;
        currentSrc = event.data.solution;
        lastObject = event.data;
        lastObject._id = $('.live-result').data('uuid');
        console.log(lastObject);
        renderSourceCode(currentSrc);
        renderComments(null);
        // register diff
        CC.registerDiffEvents(event.data._id);
      },
      function(event) {
        console.log('failed', event);
      },
    )
  };

  var rerunSolution = function(doc_id) {
    ccp.rerunSolution(doc_id,
      function(event) {
        $('.live-result').addClass(event.data.result.status);
        finished = true;
        currentSrc = event.data.solution;
        lastObject = event.data;
        lastObject._id = $('.live-result').data('uuid');
        console.log(lastObject);
        renderSourceCode(currentSrc);
        renderComments(null);
      },
      function(event) {
        console.log('failed', event);
      },
    )
  };
  
  var registerReviewEvents = function() {
    $('.hljs-ln-n').click(function(event) {
      var $this = $(this);
      var line = $this.data('line-number');

      var search = '.review-editor[data-line-number="' + line + '"]';
      var $elem = sourceCode.find(search);
      if ($elem.length) {
        $elem.remove();
        updateCounterPlaceholder();
        return;
      }

      var $tr = $this.parent().parent();
      $tr.after(
        Templates.render('review/review-editor', {
          line: line
        })
      );
      updateCounterPlaceholder();
    });
  }

  var updateCounterPlaceholder = function() {
    var cnt = $('.review-editor').length;
    $('.placeholder-comment-count').text(cnt);
    if (cnt > 0) {
      $('.finish-review').show();
    } else {
      $('.finish-review').hide();
    }
  }

  var renderComments = function(review) {
    if (review) {
      for (var line in review) {
        var search = `.hljs-ln-n[data-line-number="${line}"]`;
        var $line = sourceCode.find(search);
        if ($line.length) {
          $line.parent().parent().after(
            Templates.render('review/review-comment', {
              review: review[line],
              user: window.user.id,
            })
          );
        }
        $('.review-comment .review-comment-entry'); // .hide().slideDown(50);
        CCUtils.relativeTime($('.problem-results-holder'));
      }
    }
    $('.review-comment [data-toggle="tooltip"]').tooltip();
    onRender();
  }

  var finishReview = function() {
    var commentsTAs = $('.review-editor-comment');
    var comments = [];
    commentsTAs.each(function(i, element) {
      var $ta = $(element);
      var line = $ta.data('line-number');
      var value = $ta.val();
      if (value) {
        comments.push({
          line: line,
          comment: value
        });
      }
    });
    if (!comments.length) {
      return false;
    }

    $.ajax({
      type: 'POST',
      url: '/api/comment/add',
      dataType: 'json',
      contentType: 'application/json;charset=UTF-8',
      data: JSON.stringify({
        problem: lastObject.problem,
        course: lastObject.course,
        attempt: lastObject.attempt,
        _id: lastObject._id,
        comments: comments,
      }),
      success: function(data) {
        if (data.result == 'ok') {
          if (lastTarget) {
            lastTarget.click();
            CCUtils.loadNotifications();
          } else {
            location.reload();
          }
        }
      }
    });
    return comments;
  }

  var renderSourceCode = function(src) {
    $(sourceCodeBlock).attr('class', '');
    $(sourceCodeBlock).text(src);
    window.hljs.highlightBlock(sourceCodeBlock);
    window.hljs.lineNumbersBlock(sourceCodeBlock);
    registerReviewEvents();
    // setTimeout(registerReviewEvents, 500);
  }

  $('.live-result').click(function(event) {
    var $this = $(this);
    lastTarget = $this;
    $this.parent().parent().find('li a').removeClass('active');
    $this.addClass('active');
    current.show();
    previous.hide();
    requestReviewBtn.hide();

    if (finished) {
      renderSourceCode(currentSrc);
    } else {
      // setTimeout(submitSolution, 50);
      submitSolution();
    }
    return false;
  });

  $('.prev-result').click(function(event) {
    var $this = $(this);
    lastTarget = $this;
    $this.parent().parent().find('li a').removeClass('active');
    $this.addClass('active');
    previous.show();
    current.hide();
    requestReviewBtn.addClass('disabled alpha-5');
    previous.addClass('disabled alpha-5');

    var uuid = $this.data('uuid');
    $.ajax({
      dataType: "json",
      url: '/api/result/' + uuid,
      data: {},
      success: function(data) {
        lastObject = data;
        previous.html(
          Templates.render('process-execute', data)
        );
        var nodes = "";
        data.results.forEach((item) => {
          console.log(item);
          nodes += Templates.render('test-result2', item)
        });
        previous.find('.test-cases').html(nodes);
        previous.find('.final-evaluation').html(
          Templates.render('test-result2', data.result)
        );
        
        if (data.solution) {
            renderSourceCode(data.solution);
            renderComments(data.review);
        }
        updateCounterPlaceholder();
        previous.find('[data-toggle="tooltip"]').tooltip();
        previous.removeClass('disabled alpha-5');
        if (data.result == null) {
          console.log('broken');
          ccp.connect(function() {
            setTimeout(rerunSolution, 500, data._id);
          });
        }
        // register diff
        CC.registerDiffEvents(data._id);
      }
    });
    return false;
  });

  $('.finish-review').click(function(event) {
    finishReview();
    return false;
  });

  $('[data-toggle="popover"]').popover();

  // send a socket or load a result
  if (_id) {
    cc.connect(function() {
      setTimeout(submitSolution, 500);
    });
  } else {
    var active = $('.prev-result.active');
    if (active.length) {
      active.click();
    } else {
      var first = $('.prev-result');
      if (first.length) {
        $(first.get(0)).click();
      } else {
        $('.problem-results-holder').html(
          '<div class="white col-12 p-3"><h1>No results found</h1></div>'
        );
      }
    }
  }
});
