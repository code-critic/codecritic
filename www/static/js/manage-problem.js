var __spreadArrays = (this && this.__spreadArrays) || function () {
    for (var s = 0, i = 0, il = arguments.length; i < il; i++) s += arguments[i].length;
    for (var r = Array(s), k = 0, i = 0; i < il; i++)
        for (var a = arguments[i], j = 0, jl = a.length; j < jl; j++, k++)
            r[k] = a[j];
    return r;
};
$(document).ready(function () {
    var $inputForm = $('#generate-input-form');
    var $outputForm = $('#generate-output-form');
    var $searchForm = $('#search-form');
    var $referenceForm = $('#reference-form');
    var $adminZone = $('#admin-zone');
    var $target = $adminZone.find('.solution-result .result');
    var courseID = $adminZone.data('course');
    var problemID = $adminZone.data('problem');
    var problems = $adminZone.data('problem-ids').split(",");
    var resultCanvas = $('.search-results');
    var sourceCode = null;
    var languageID = null;
    var tags = window.course.tags;
    var cc = new CC($target);
    var F = function (name, desc, icon, value, options, classes, type) {
        if (icon === void 0) { icon = null; }
        if (value === void 0) { value = null; }
        if (options === void 0) { options = []; }
        if (classes === void 0) { classes = null; }
        if (type === void 0) { type = 'select'; }
        return {
            name: name,
            desc: desc,
            icon: icon,
            type: type,
            value: value,
            options: options,
            classes: classes
        };
    };
    var filters = [
        F('problem', 'Problem', 'code', problemID, ['all'].concat(problems)),
        F('daterange', 'Date range', 'calendar', 'week', ['day', 'week', 'two weeks', 'month', 'all']),
        F('limit-per-user', 'of attempts', 'hashtag', '3', ['1', '3', '5', 'all']),
        F('has-review-flag', 'Has review flag', 'flag', 'all', ['yes', 'no', 'all']),
        F('sort-by-outer', 'Sort students', 'sort-amount-up', 'lastname', ['firstname', 'lastname']),
        F('sort-by-inner', 'Sort attempts', 'sort-amount-up', 'result.score', ['result.score', '_id']),
        F('status', 'Exit status', 'check', 'all', ['answer-correct', 'answer-correct-timeout', 'answer-wrong', 'all'], 'col-12 col-md-4'),
    ];
    filters = __spreadArrays(filters, tags.map(function (i) { return F("tag-" + i.name, i.name, 'hashtag', 'all', __spreadArrays(['all'], i.values)); }), [
        F('search', 'Search', 'search', null, null, null, 'search'),
        F('refresh', 'Refresh', null, null, null, null, 'refresh'),
    ]);
    var $lastResultsNav = $('#last-results-nav');
    var $lastResultsTab = $('#last-results-tab');
    CCUtils.enableTooltips($lastResultsNav.find('.filters').html(Templates.render('admin/filters', { filters: filters })));
    // ---------------------------------------------------------------------------
    var collectFilters = function () {
        var result = {};
        for (var _i = 0, filters_1 = filters; _i < filters_1.length; _i++) {
            var f = filters_1[_i];
            var $item = $lastResultsNav.find('#filter-' + f.name);
            result[f.name] = $item.val();
        }
        return result;
    };
    var loadData = function () {
        var config = {
            course: courseID,
            problem: problemID,
            filters: collectFilters()
        };
        resultCanvas.addClass('disabled alpha-5');
        $.ajax({
            type: 'POST',
            dataType: "json",
            url: '/api/stats',
            contentType: 'application/json;charset=UTF-8',
            data: JSON.stringify(config),
            success: function (data) {
                resultCanvas.removeClass('disabled alpha-5');
                console.log(config);
                resultCanvas.html(Templates.render('admin/user-results', { users: data, config: config }));
                CCUtils.relativeTime(resultCanvas);
                CCUtils.enableTooltips(resultCanvas);
                $('#table_id').DataTable({
                    searching: false,
                    paging: false,
                    info: false,
                    autoWidth: false,
                    order: []
                });
                $('.element-link').click(function () {
                    window.open($(this).data('href'), '_blank');
                });
            },
            error: function (xhr, ajaxOptions, thrownError) {
                alert(xhr.status);
                alert(thrownError);
            }
        });
    };
    // ---------------------------------------------------------------------------
    $inputForm.submit(function () {
        $adminZone.find('.solution-result').show();
        var $form = $(this);
        $form.addClass('disabled');
        var actionType = 'generate-input';
        var useDocker = $form.find('.input-use-docker').is(':checked');
        cc.submitSolution(courseID, problemID, languageID, sourceCode, actionType, useDocker, function (event) {
            $form.removeClass('disabled');
        }, function (event) {
            $form.removeClass('disabled');
        });
        return false;
    });
    $outputForm.submit(function () {
        $adminZone.find('.solution-result').show();
        var $form = $(this);
        $form.addClass('disabled');
        var actionType = 'generate-output';
        var useDocker = $form.find('.input-use-docker').is(':checked');
        cc.submitSolution(courseID, problemID, languageID, sourceCode, actionType, useDocker, function (event) {
            $form.removeClass('disabled');
        });
        return false;
    });
    $searchForm.submit(function () {
        return false;
    });
    $lastResultsTab.on('show.bs.tab', function (e) {
        loadData();
    });
    $lastResultsNav.find('.filters .filter-item').change(function () {
        loadData();
    });
    $('.btn-search').click(function () {
        loadData();
    });
    // ---------------------------------------------------------------------------
    cc.connect();
    loadData();
});
//# sourceMappingURL=manage-problem.js.map