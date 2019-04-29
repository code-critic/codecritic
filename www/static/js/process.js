$(document).ready(function() {
  
  var cc = new CC($('#solution-result'));
  var submitSolution = function() {
    cc.processSolution(
      $('#solution-result').data('uuid'),
      function() {
        console.log('success');
      },
      function() {
        console.log('failed');
      },
    )
  };
  
  Globals.initEnv();
  Templates.loadTemplates();
  cc.connect(function(){
    console.log('ok');
    setTimeout(submitSolution, 500);
  });
  // var func = function(socket) {
  //   console.log('submitting');
  //   Automatest.processSolution(
  //     socket,
  //     $('#solution-result').data('uuid'),
  //     function(event) {
  //       console.log('k, done');
  //     })
  // };
  // 
  // // Automatest.openSocket(function(socket) {
  // //   Automatest.setTarget($('#solution-result'));
  // //   console.log(socket);
  // //   setTimeout(func, 1000, socket);
  // // });
  // window.func = func;
});
