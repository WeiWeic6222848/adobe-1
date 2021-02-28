(function ($) {
    // USE STRICT
    "use strict";

    $(".form-radio .radio-item").click(function () {
        //Spot switcher:
        $(this).parent().find(".radio-item").removeClass("active");
        $(this).addClass("active");
    });

    $('#role_type').parent().append('<ul class="list-item" id="newrole_type" name="role_type"></ul>');
    $('#role_type option').each(function () {
        $('#newrole_type').append('<li value="' + $(this).val() + '">' + $(this).text() + '</li>');
    });
    $('#role_type').remove();
    $('#newrole_type').attr('id', 'role_type');
    $('#role_type li').first().addClass('init');
    $("#role_type").on("click", ".init", function () {
        $(this).closest("#role_type").children('li:not(.init)').toggle('slow');
    });

    var allOptions = $("#role_type").children('li:not(.init)');
    $("#role_type").on("click", "li:not(.init)", function () {
        allOptions.removeClass('role-selected');
        allOptions.removeClass('selected');
        $(this).addClass('role-selected');
        $(this).addClass('selected');
        $("#role_type").children('.init').html($(this).html());
        $("#role_type").children('.init').attr("value",$(this).attr('value'));
        if ($(this).attr('value')==="2"){
            $("#name").removeClass('hidden');
            $("#name").val("");
        }
        else{
            $("#name").addClass('hidden');
            $("#name").val("filled");
        }
        allOptions.toggle('slow');
    });

})(jQuery);
