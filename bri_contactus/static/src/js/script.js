$(document).foundation('interchange', {
    named_queries: {
        mobile: 'only screen and (min-width: 1px)',
        tablet: 'only screen and (min-width: 768px)',
        pc: 'only screen and (min-width: 992px)',
        large: 'only screen and (min-width: 1200px)'
    }
});

var otherBool = false;
var formSend = false;

$(document).ready(function () {

    $("#terms").prop('checked', false);

    $("#bmw-form").submit(function (e) {
        if (!validateForm()) {
            e.preventDefault();
            return false;
        } else {
            if (formSend) {
                e.preventDefault();
                return false;
            }
            $("#bmw-form .btn").addClass("disabled");
            formSend = true;
        }
    });

    $("#bmw-form #media").change(function () {
        if ($(this).val() === "Otros") {
            $("#bmw-form #other-media").removeClass("hidden");
            otherBool = true;
        } else {
            $("#bmw-form #other-media").addClass("hidden");
            otherBool = false;
        }
    });
});

function validateForm() {
    error = 0;
    firstName = "#bmw-form #first-name";
    lastName = "#bmw-form #last-name";
    email = "#bmw-form #email";
    phone = "#bmw-form #phone";
    department = "#bmw-form #department";
    model = "#bmw-form #model";
    media = "#bmw-form #media";
    otherMedia = "#bmw-form #other-media";
    terms = "#bmw-form #terms";
    //Retrollamadas
    address = "#bmw-form #address";
    chassis = "#bmw-form #chassis";
    year = "#bmw-form #year";
    ///Retrollamadas

    if ($(firstName).size() > 0) {
        if ($(firstName).val().length < 1) {
            $(firstName).parent().parent().children('.error-block').children('.label-danger').removeClass("hidden");
            error++;
        } else {
            $(firstName).parent().parent().children('.error-block').children('.label-danger').addClass("hidden");
        }
    }

    if ($(lastName).size() > 0) {
        if ($(lastName).val().length < 1) {
            $(lastName).parent().parent().children('.error-block').children('.label-danger').removeClass("hidden");
            error++;
        } else {
            $(lastName).parent().parent().children('.error-block').children('.label-danger').addClass("hidden");
        }
    }

    if ($(email).size() > 0) {
        pattern = new RegExp(/^([\w-\.]+@([\w-]+\.)+[\w-]{2,4})?$/);
        if ($(email).val().length < 4 || !pattern.test($(email).val())) {
            $(email).parent().parent().children('.error-block').children('.label-danger').removeClass("hidden");
            error++;
        } else {
            $(email).parent().parent().children('.error-block').children('.label-danger').addClass("hidden");
        }
    }
    if ($(phone).size() > 0) {
        if ($(phone).val().length < 4) {
            $(phone).parent().parent().children('.error-block').children('.label-danger').removeClass("hidden");
            error++;
        } else {
            $(phone).parent().parent().children('.error-block').children('.label-danger').addClass("hidden");
        }
    }

    if ($(department).size() > 0) {
        if ($(department).val().length < 1) {
            $(department).parent().parent().children('.error-block').children('.label-danger').removeClass("hidden");
            error++;
        } else {
            $(department).parent().parent().children('.error-block').children('.label-danger').addClass("hidden");
        }
    }

    if ($(model).size() > 0) {
        if ($(model).val().length < 1) {
            $(model).parent().parent().children('.error-block').children('.label-danger').removeClass("hidden");
            error++;
        } else {
            $(model).parent().parent().children('.error-block').children('.label-danger').addClass("hidden");
        }
    }

    if ($(media).size() > 0) {
        if ($(media).val().length < 1) {
            $(media).parent().parent().children('.error-block').children('.label-danger').removeClass("hidden");
            error++;
        } else {
            $(media).parent().parent().children('.error-block').children('.label-danger').addClass("hidden");
        }
    }

    if (otherBool) {
        if ($(otherMedia + " .other").val().length < 1) {
            $(otherMedia + " .error-block .label-danger").removeClass("hidden");
            error++;
        } else {
            $(otherMedia + " .error-block .label-danger").addClass("hidden");
        }
    }

    if ($(terms).size() > 0) {
        if (!$(terms).is(':checked')) {
            $(terms).parent().parent().parent().parent().children('.error-block').children('.label-danger').removeClass("hidden");
            error++;
        } else {
            $(terms).parent().parent().parent().parent().children('.error-block').children('.label-danger').addClass("hidden");
        }
    }

    //Retrollamadas
    if ($(address).size() > 0) {
        if ($(address).val().length < 1) {
            $(address).parent().parent().children('.error-block').children('.label-danger').removeClass("hidden");
            error++;
        } else {
            $(address).parent().parent().children('.error-block').children('.label-danger').addClass("hidden");
        }
    }

    if ($(chassis).size() > 0) {
        if ($(chassis).val().length !== 7) {
            $(chassis).parent().parent().children('.error-block').children('.label-danger').removeClass("hidden");
            error++;
        } else {
            $(chassis).parent().parent().children('.error-block').children('.label-danger').addClass("hidden");
        }
    }
    
    if ($(year).size() > 0) {
        if ($(year).val().length < 1) {
            $(year).parent().parent().children('.error-block').children('.label-danger').removeClass("hidden");
            error++;
        } else {
            $(year).parent().parent().children('.error-block').children('.label-danger').addClass("hidden");
        }
    }
    ///Retrollamadas

    if (error > 0) {
        return false;
    } else {
        return true;
    }
}
