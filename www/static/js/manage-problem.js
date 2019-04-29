$(document).ready(function() {
  var $inputForm = $('#generate-input-form');
  var $outputForm = $('#generate-output-form');
  var $referenceForm = $('#reference-form');
  var $adminZone = $('#admin-zone');

  var $target = $adminZone.find('.solution-result .result');
  var courseID = $adminZone.data('course');
  var problemID = $adminZone.data('problem');
  var sourceCode = null;
  var languageID = null;
  Globals.initEnv();
  Templates.loadTemplates();
  
  
  var cc = new CC($target);
  cc.connect(function(){
    console.log('ok, connected');
  });

  $inputForm.submit(function() {
    $adminZone.find('.solution-result').show();
    var $form = $(this);
    $form.addClass('disabled');

    var actionType = 'generate-input';
    var useDocker = $form.find('.input-use-docker').is(':checked');
    cc.submitSolution(
      courseID, problemID, languageID, sourceCode, actionType, useDocker,
      function(event) {
        $form.removeClass('disabled');
      },
      function(event) {
        $form.removeClass('disabled');
      }
    );
    return false;
  });

  $outputForm.submit(function() {
    $adminZone.find('.solution-result').show();
    var $form = $(this);
    $form.addClass('disabled');

    var actionType = 'generate-output';
    var useDocker = $form.find('.input-use-docker').is(':checked');
    cc.submitSolution(
      courseID, problemID, languageID, sourceCode, actionType, useDocker,
      function(event) {
        $form.removeClass('disabled');
      }
    );
    return false;
  });

  // var $referenceNav = $('#reference-nav');
  // var $referenceTab = $('#reference-tab');
  // $referenceNav.html(
  //   nunjucks.render('static/templates/process-execute.njk', _showcase)
  // );
  
  
  var $lastResultsNav = $('#last-results-nav');
  var $lastResultsTab = $('#last-results-tab');
  
  $lastResultsTab.on('show.bs.tab', function(e) {
    $.ajax({
      dataType: "json",
      url: '/stats',
      data: {
        courseID: courseID,
        problemID: problemID
      },
      success: function(data) {
        $lastResultsNav.html(
          nunjucks.render('static/templates/user-stats.njk', {items: data})
        );
      }
    });
  });
});
