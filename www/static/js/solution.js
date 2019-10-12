$(document).ready(function () {
    var adminOnly = '<i class="fas fa-user-shield" data-toggle="tooltip" title="Visible to admin only"></i> ';
    var isAdmin = $(document.body).hasClass('admin');
    var editor = window.ace.edit("editor");
    var $mainContent = $('#main-content');
    var courseID = $('.prob-select').data('course');
    var cs = CCUtils.courseStorage(courseID);
    var saveTimeout = null;
    var srcStatus = $('.src-status');
    var $target = $('.solution-result');
    var ONE_DAY = 86400;
    var ONE_WEEK = ONE_DAY * 7;
    var ONE_MONTH = ONE_DAY * 31;
    var ONE_YEAR = ONE_DAY * 365;
    var category = null;
    $('.count-down').each(function (index, item) {
        var $item = $(item);
        var timeLeft = Number($item.data('time-left'));
        var m = window.moment().locale('en').add(timeLeft, 'seconds');
        if (timeLeft > 0) {
            if (timeLeft < ONE_WEEK) {
                $item.html('The submission will be closed <strong>' +
                    m.fromNow() +
                    '</strong>' +
                    ' (' + m.format('llll') + ')').addClass('prob-almost-over');
            }
            else if (isAdmin) {
                $item.html(adminOnly + 'The submission will be closed <strong>' +
                    m.fromNow() +
                    '</strong>' +
                    ' (' + m.format('llll') + ')').addClass('prob-admin-over');
            }
        }
        else {
            $item.html('The submission is closed <strong>' +
                m.fromNow()).addClass('prob-over');
        }
    });
    editor.setTheme("ace/theme/github");
    editor.setOptions({
        enableBasicAutocompletion: true,
        enableSnippets: true,
        enableLiveAutocompletion: true
    });
    editor.session.on('change', function () {
        if (saveTimeout) {
            clearTimeout(saveTimeout);
            saveTimeout = null;
        }
        srcStatus.html('(saving)');
        saveTimeout = setTimeout(saveCode, 1000);
        $('#srcTA').val(editor.getValue());
    });
    $('#editor').append('<span class="btn btn-link fullscreen" data-toggle="tooltip" title="Toggle fullscreen"><i class="fas fa-expand"></i></span>');
    $('#editor .btn.fullscreen').click(function () {
        $('#editor').toggleClass('fullscreen');
        window.dispatchEvent(new Event('resize'));
    });
    var loadLocalStorage = function () {
        var problemID = cs.storageGet('problemID');
        var languageID = cs.storageGet('languageID');
        var key = [problemID, languageID];
        var sourceCode = cs.storageGet(key.concat('sourceCode'));
        if (problemID) {
            $('.prob-select').val(problemID);
        }
        if (languageID) {
            $('.lang-select').val(languageID);
        }
        if (sourceCode) {
            editor.setValue(sourceCode, 1);
        }
    };
    var saveProblemAndLang = function () {
        var problemID = $('.prob-select').val();
        var languageID = $('.lang-select').val();
        cs.storagePut('problemID', problemID);
        cs.storagePut('languageID', languageID);
    };
    var loadProblemAndLang = function () {
        var problemID = cs.storageGet('problemID');
        var languageID = cs.storageGet('languageID');
        if (problemID) {
            $('.prob-select').val(problemID);
            $('.prob-select').trigger('change');
        }
        if (languageID) {
            $('.lang-select').val(languageID);
            $('.prob-select').trigger('change');
        }
    };
    var saveCode = function () {
        var problemID = $('.prob-select').val();
        var languageID = $('.lang-select').val();
        var key = [problemID, languageID];
        var sourceCode = editor.getValue();
        cs.storagePut(key.concat('sourceCode'), sourceCode);
        srcStatus.html('(saved)');
    };
    var loadCode = function () {
        var problemID = cs.storageGet('problemID');
        var languageID = cs.storageGet('languageID');
        var key = [problemID, languageID];
        var sourceCode = cs.storageGet(key.concat('sourceCode'));
        if (sourceCode) {
            editor.setValue(sourceCode, 1);
        }
    };
    $('.lang-select').change(function () {
        var langID = $(this).val();
        var langName = $(this).find(`option[value="${langID}"]`).data('name');
        var langStyle = $(this).find(`option[value="${langID}"]`).data('style');
        editor.session.setMode('ace/mode/' + langStyle);
        $('.lang-name-placeholder').text(langName);
        $('.lang-id-placeholder').text(langID);
        $('.lang-style-placeholder').text(langStyle);
        saveProblemAndLang();
        loadCode();
    });
    $('.view-lang-example-link').click(function () {
        var href = $(this).data('href');
        var langID = $('.lang-select').val();
        var langStyle = $('.lang-select').find(`option[value="${langID}"]`).data('style');
        editor.session.setMode('ace/mode/' + langStyle);
        editor.setValue(LangExamples.examples[langID], 1);
        editor.focus();
    });
    $('.cat-select').change(function () {
        category = $(this).val();
        const isCat = `option[data-problem-cat="${category}"]`;
        const isNotCat = `option[data-problem-cat!="${category}"]`;
        const isCatOptions = $('.prob-select').find(isCat);
        isCatOptions.show();
        $('.prob-select').find(isNotCat).hide();
        var firstVisible = $($('.prob-select').find('option:not(:hidden)').get(0));
        $('.prob-select')
            .val(firstVisible.val())
            .trigger('change');
    });
    $('.prob-select').change(function () {
        var problemID = $(this).val();
        var problemName = $(this).find('option[value="' + problemID + '"]').data('problem-name');
        var $id = $('#desc-' + problemID);
        $('.prob-desc').addClass('d-none');
        $id.removeClass('d-none');
        var elms = '#editor, form button, .lang-select';
        var timeLeft = Number($id.data('time-left'));
        if (timeLeft > 0) {
            $(elms).css('opacity', '1.0').removeClass('disabled').show('normal');
        }
        else {
            $(elms).addClass('disabled').css('opacity', '0.5');
        }
        $('.manage-problem-link').attr('href', $('.manage-problem-link').data('href') + $(this).val());
        $('.view-result-link').attr('href', $('.view-result-link').data('href') + $(this).val());
        $('.prolem-name-placeholder').text(problemName);
        $('.prolem-id-placeholder').text(problemID);
        saveProblemAndLang();
        loadCode();
    });
    $('[data-toggle="tooltip"]').tooltip();
    loadProblemAndLang();
    loadCode();
    $('.prob-select').trigger('change');
    $('.lang-select').trigger('change');
    $('.cat-select').trigger('change');
    CCUtils.registerDnD($('#submit-solution .src-group'), function (file, data) {
        try {
            var ext = file.name.split('.').slice(-1)[0];
            var style = $('option[data-ext="' + ext + '"]').val();
            $('.lang-select').val(style);
            editor.session.setMode('ace/mode/' + style);
            editor.setValue(data, 1);
        }
        catch (e) {
            console.log(e);
        }
    });
});
//# sourceMappingURL=solution.js.map