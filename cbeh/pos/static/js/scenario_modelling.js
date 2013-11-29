if(window.pos === undefined) {
    window.pos = {};
}

if(window.pos.scenario_modelling === undefined) {
    window.pos.scenario_modelling = {};
}


// Store the project's PK for any later requests to the server
window.pos.scenario_modelling.store_project_pk = function(project_pk) {
    window.pos.scenario_modelling.project_pk = project_pk;
};

// Set value if user has clicked the calculate button
window.pos.scenario_modelling.calculate_clicked = function() {
    window.pos.scenario_modelling.calculate_clicked = false;
};

// Set click handlers to reset the modifiable inputs with original data
window.pos.scenario_modelling.set_click_handlers = function() {

    // Reset Areas
    jQuery("#reset_areas_button").click(function() {
        pos.scenario_modelling.reset_areas();
    });
    // Reset Population Numbers
    jQuery("#reset_populations_button").click(function() {
        pos.scenario_modelling.reset_populations();
    });
    // Calculate metrics
    jQuery("#calculate_button").click(function() {
        window.pos.scenario_modelling.calculate_clicked = true;
        pos.scenario_modelling.calculate_metrics();
    });
    // Save the modified stat data
    jQuery("#save_stat_button").click(function() {
        pos.scenario_modelling.save_modified_stats();
    });

};

// Send request to server to save the user entered stats
window.pos.scenario_modelling.save_modified_stats = function() {

    var area_list = pos.get_altered_areas_data();
    var pop_list = pos.get_altered_population_data();

    // AJAX Setup, get the CSRF cookie (before making POST)
    jQuery.ajaxSetup({
        beforeSend: function(xhr, settings) {
            function getCookie(name) {
                var cookieValue = null;
                    if(document.cookie && document.cookie !== '') {
                        var cookies = document.cookie.split(';');
                        for (var i = 0; i < cookies.length; i++) {
                            var cookie = jQuery.trim(cookies[i]);
                            // Does this cookie string begin with the name we want?
                            if(cookie.substring(0, name.length + 1) === (name + '=')) {
                                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                                break;
                            }
                        }
                    }
                return cookieValue;
            }
            if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
                // Only send the token to relative URLs i.e. locally.
                xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
            }
        }
    });

    // Make POST with AJAX
    var request = jQuery.ajax({
        url: '/cbeh/pos/user_stats/save_modified_stats/',
        type: "post",
        dataType: 'json',
        data: {
            area_list: area_list,
            pop_list: pop_list,
            project_pk: pos.scenario_modelling.project_pk
        }
    });

    request.done(function(data) {
        // Give feedback messages
        var message;
        if(data[0] === false) {
            message = 'Please check the area values you entered. Allowable values are numbers only (square metres).';
            jQuery.jGrowl(message, {
                header: 'Warning: Problem with altered areas',
                position: 'top-right',
                sticky: true
            });
        }
        if(data[1] === false) {
            message ='Please check the population values you entered. Allowable values are whole numbers only (no decimals).';
            jQuery.jGrowl(message, {
                header: 'Warning: Problem with altered populations',
                position: 'top-right',
                sticky: true
            });
        }
         if(data[0] === true && data[1] === true) {
            message ='Statistics data has been saved.';
            jQuery.jGrowl(message, {
                header: 'Success:',
                position: 'top-right',
                sticky: false,
                life: 3000
            });
         }

    });

};

// Send request to server to calculate metrics
window.pos.scenario_modelling.calculate_metrics = function() {

    var area_list = pos.get_altered_areas_data();
    var pop_list = pos.get_altered_population_data();

    // Make GET with AJAX
    jQuery.get('/cbeh/pos/user_stats/calculate_metrics/', {
        area_list: area_list,
        population_list: pop_list
    })
        .done(function(data) {
            // Place data into corresponding elements if everything is good
            var message;
            if(data[0] === false) {
                message = 'Please check the area values you entered. Allowable values are numbers only (square metres).';
                jQuery.jGrowl(message, {
                    header: 'Warning: Problem with altered areas',
                    position: 'top-right',
                    sticky: true
                });
            }
            if(data[1] === false) {
                message ='Please check the population values you entered. Allowable values are whole numbers only (no decimals).';
                jQuery.jGrowl(message, {
                    header: 'Warning: Problem with altered populations',
                    position: 'top-right',
                    sticky: true
                });
            }
            if(data[0] !== false && data[1] !== false) {
                // Create keys mapping to match list data with rows
                var keys = [
                    '0_4_row',
                    '5_14_row',
                    '15_19_row',
                    '20_24_row',
                    '25_34_row',
                    '35_44_row',
                    '45_54_row',
                    '55_64_row',
                    '65_74_row',
                    '75_84_row',
                    '85_plus_row',
                    'total_pop_row'
                ];
                var key, i, j, str_j;

                for (i=0; i<12; i++) {
                    key = keys[i];
                    for (j=5; j<14; j++) {
                        str_j = j.toString();
                        jQuery("#" + key + " td:nth-child(" + str_j + ")").text(data[2][i][j-5]);
                    }
                }
                // If user clicked calculate, show success feedback
                if(window.pos.scenario_modelling.calculate_clicked === true) {
                    message ='Metrics have been updated in the table below.';
                    jQuery.jGrowl(message, {
                        header: 'Success:',
                        position: 'top-right',
                        sticky: false,
                        life: 3000
                    });
                }
            }
        });
};

// Reset the Areas
window.pos.scenario_modelling.reset_areas = function() {

    // Make GET with AJAX
    jQuery.get('/cbeh/pos/user_stats/reset_areas/', {
        project_pk: pos.scenario_modelling.project_pk
    })
        .done(function(data) {
            // Place data into corresponding elements
            jQuery('#all_parks').val(data.all_parks);
            jQuery('#pocket_park').val(data.pocket_parks);
            jQuery('#small_park').val(data.small_parks);
            jQuery('#medium_park').val(data.medium_parks);
            jQuery('#large_park_1').val(data.large_parks_1);
            jQuery('#large_park_2').val(data.large_parks_2);
            jQuery('#district_park_1').val(data.district_parks_1);
            jQuery('#district_park_2').val(data.district_parks_2);
            jQuery('#regional_open_space').val(data.regional_parks);
        });
};

// Reset the Populations Numbers
window.pos.scenario_modelling.reset_populations = function() {

    // Make GET with AJAX
    jQuery.get('/cbeh/pos/user_stats/reset_populations/', {
        project_pk: pos.scenario_modelling.project_pk
    })
        .done(function(data) {
            // Place data into corresponding elements
            jQuery('#pop_0_4').val(data.age_0_4);
            jQuery('#pop_5_14').val(data.age_5_14);
            jQuery('#pop_15_19').val(data.age_15_19);
            jQuery('#pop_20_24').val(data.age_20_24);
            jQuery('#pop_25_34').val(data.age_25_34);
            jQuery('#pop_35_44').val(data.age_35_44);
            jQuery('#pop_45_54').val(data.age_45_54);
            jQuery('#pop_55_64').val(data.age_55_64);
            jQuery('#pop_65_74').val(data.age_65_74);
            jQuery('#pop_75_84').val(data.age_75_84);
            jQuery('#pop_85_plus').val(data.age_85_plus);
            jQuery('#pop_total').val(data.total_pop);
        });

};

window.pos.get_altered_areas_data = function() {
    // Group the data into a list
    var area_list = [
        jQuery('#all_parks').val(),
        jQuery('#pocket_park').val(),
        jQuery('#small_park').val(),
        jQuery('#medium_park').val(),
        jQuery('#large_park_1').val(),
        jQuery('#large_park_2').val(),
        jQuery('#district_park_1').val(),
        jQuery('#district_park_2').val(),
        jQuery('#regional_open_space').val()
    ];
    return area_list;
};

window.pos.get_altered_population_data = function() {
    // Group the data into a list
    var pop_list = [
        jQuery('#pop_0_4').val(),
        jQuery('#pop_5_14').val(),
        jQuery('#pop_15_19').val(),
        jQuery('#pop_20_24').val(),
        jQuery('#pop_25_34').val(),
        jQuery('#pop_35_44').val(),
        jQuery('#pop_45_54').val(),
        jQuery('#pop_55_64').val(),
        jQuery('#pop_65_74').val(),
        jQuery('#pop_75_84').val(),
        jQuery('#pop_85_plus').val(),
        jQuery('#pop_total').val()
    ];
    return pop_list;
};
