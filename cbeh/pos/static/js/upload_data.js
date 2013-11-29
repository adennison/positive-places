if(window.pos === undefined) {
    window.pos = {};
}

if(window.pos.upload_data === undefined) {
    window.pos.upload_data = {};
}


// Set click handlers to reset the modifiable inputs with original data
// and also to display the upload progress bar
window.pos.upload_data.set_click_handlers = function() {

    // Calculate LGA Stats
    jQuery("#calculate_lga_stats").click(function() {
        pos.upload_data.display_upload_progress();
        pos.upload_data.calculate_lga_stats();
    });

    // Calculate Suburb Stats
    jQuery("#calculate_suburb_stats").click(function() {
        pos.upload_data.display_upload_progress();
        pos.upload_data.calculate_suburb_stats();
    });

    // Calculate Facility Stats (LGAs & Suburbs)
    jQuery("#calculate_facility_stats").click(function() {
        pos.upload_data.display_upload_progress();
        pos.upload_data.calculate_facility_stats();
    });

    // Display Upload progress bar
    jQuery("#submit_button").click(function() {
        pos.upload_data.display_upload_progress();
    });

};

// Send request to server to calculate LGA stats
window.pos.upload_data.calculate_lga_stats = function() {

    // Make GET with AJAX
    jQuery.get('/cbeh/pos/user_stats/calculate_lga_stats/', {
    })
        .done(function(data) {
            pos.upload_data.hide_upload_progress();
            // Show success feedback
            message ='LGA area, population and catchment statistics have been calculated.';
            jQuery.jGrowl(message, {
                header: 'Success:',
                position: 'top-right',
                sticky: true
            });
        });
};

// Send request to server to calculate Suburb stats
window.pos.upload_data.calculate_suburb_stats = function() {

    // Make GET with AJAX
    jQuery.get('/cbeh/pos/user_stats/calculate_suburb_stats/', {
    })
        .done(function(data) {
            pos.upload_data.hide_upload_progress();
            // Show success feedback
            message ='Suburb area, population and catchment statistics have been calculated.';
            jQuery.jGrowl(message, {
                header: 'Success:',
                position: 'top-right',
                sticky: true
            });
        });
};

// Send request to server to calculate Facility stats (LGAs and Suburbs)
window.pos.upload_data.calculate_facility_stats = function() {

    // Make GET with AJAX
    jQuery.get('/cbeh/pos/user_stats/calculate_facility_stats/', {
    })
        .done(function(data) {
            pos.upload_data.hide_upload_progress();
            // Show success feedback
            message ='LGA and Suburb facility statistics have been calculated.';
            jQuery.jGrowl(message, {
                header: 'Success:',
                position: 'top-right',
                sticky: true
            });
        });
};

// On submit button display the upload progress info to the user
window.pos.upload_data.display_upload_progress = function(event) {
    jQuery('#progress_display_1').css("display", "inline-block");
    jQuery('#upload_text_1').css("display", "inline-block");
};

// Hide upload progress from the user
// After bad user upload attempt or finish copying user stats from LGA/Suburb
window.pos.upload_data.hide_upload_progress = function(event) {
    jQuery('#progress_display_1').css("display", "none");
    jQuery('#upload_text_1').css("display", "none");
};
