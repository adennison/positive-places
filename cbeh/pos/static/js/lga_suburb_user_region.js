if(window.pos === undefined) {
    window.pos = {};
}

if(window.pos.lga_suburb_user_region === undefined) {
    window.pos.lga_suburb_user_region = {};
}


// Store values passed in from view
window.pos.lga_suburb_user_region.store_wkt = function(wkt) {

    pos.lga_suburb_user_region.wkt = wkt;
};

// Set up autocomplete search box for LGA / Suburb
window.pos.lga_suburb_user_region.search_box = function() {

    if (pos.lga_suburb_user_region.wkt === 'false') {
        pos.lga_suburb_user_region.disable_stats_buttons();
    } else {
        // Update the link for View Stats button, there is data available
        var region_pk = jQuery("#user_region_pk").val();
        var view_stats_button_attributes = jQuery("a#view_stats_button")[0].attributes;
        for (var i=0; i < view_stats_button_attributes.length; i++) {
            if (view_stats_button_attributes[i].name === 'href') {
                var from_region_pk = jQuery("#region_values").val();
                view_stats_button_attributes[i].value = '/cbeh/pos/region/' + region_pk;
            }
        }
    }

    jQuery("#region_labels").autocomplete({
        source: "/cbeh/pos/search/?look=region_autocomplete",
        minLength: 3,
        delay: 400,
        autoFocus: false,
        focus: function(event, ui) {
            jQuery("#region_labels").val(ui.item.label);
            return false;
        },
        select: function(event, ui) {
            jQuery("#region_labels").val(ui.item.label);
            jQuery("#region_values").val(ui.item.value);
            // Disable the View Stats & Scneario Calculator buttons
            // In case they have been enabled from a previous user search
            pos.lga_suburb_user_region.toggle_bootstrap_anchor_button("view_stats_button", false);
            pos.toggle_bootstrap_anchor_button('scenario_calculator_button', false);
            // Load the progress bar to show something is happening
            window.pos.display_upload_progress();
            // Update the link on the View Stats button
            var region_pk = jQuery("#user_region_pk").val();
            var view_stats_button_attributes = jQuery("a#view_stats_button")[0].attributes;
            for (var i=0; i < view_stats_button_attributes.length; i++) {
                if (view_stats_button_attributes[i].name === 'href') {
                    var from_region_pk = jQuery("#region_values").val();
                    view_stats_button_attributes[i].value = '/cbeh/pos/region/' + region_pk;
                }
            }
            // Calculate the scenario data
            pos.lga_suburb_user_region.scenario_calculations(region_pk, from_region_pk);
            return false;
        }
    });
};


// Do the scenario calculations & copy Area/Pop Stats for the region
window.pos.lga_suburb_user_region.scenario_calculations = function(user_region_pk, from_region_pk) {

        // AJAX Setup, get the CSRF cookie
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
            url: "/cbeh/pos/user_region/save_user_region_polygon/",
            type: "post",
            dataType: 'json',
            data: {
                wkt: 'from_existing_region',
                user_region_pk: user_region_pk,
                from_region_pk: from_region_pk
            }
        });

        request.done(function (json_list) {
            // Check if there is any problem with saving the polygon
            // Alert the message to the user
            if (json_list.issue) {
                // jQuery.jGrowl(json_list.message, {
                //     header: 'Warning',
                //     position: 'top-right',
                //     sticky: false,
                //     life: 10000
                // });
            } else {
                // jQuery.jGrowl("Your region has been saved!", {
                //     header: 'Success',
                //     position: 'top-right',
                //     sticky: true
                // });
                // Hide the progress bar
                window.pos.hide_upload_progress();
                // Allow user to access stats data
                pos.lga_suburb_user_region.toggle_bootstrap_anchor_button("view_stats_button", true);
                pos.toggle_bootstrap_anchor_button('scenario_calculator_button', true);
            }
        });

};

// Prevent form being submitted if user presses 'Enter' key in a text box
// window.pos.lga_suburb_user_region.disableEnterKey = function(e, buttonID) {
window.pos.lga_suburb_user_region.disableEnterKey = function(e) {
    var key; // Variable to hold the number of the key that was pressed
    //if the browser is Internet Explorer
    if(window.event){
        key = window.event.keyCode; // Store the key code (Key number) of the pressed key
    } else {
        key = e.which;
    }
    // If key 13 is pressed (the 'Enter' key) and search button is disabled
    // if ((key == 13) && (document.getElementById(buttonID).disabled == true)) {
    if (key == 13) {
        return false; // Do nothing
    } else {
    return true; // Continue as normal (allow the key press)
    }
};

// Disable View Stats & Scenario Calculator buttons
// before any LGA or Suburn has been selected
window.pos.lga_suburb_user_region.disable_stats_buttons = function() {
    pos.toggle_bootstrap_anchor_button('view_stats_button', false);
    pos.toggle_bootstrap_anchor_button('scenario_calculator_button', false);

};

// Enable/Disable a bootstrap 'href' button by its ID.
// 'bool' input: true if enabling, false if disabling
window.pos.lga_suburb_user_region.toggle_bootstrap_anchor_button = function(id, bool) {
    var jquery_id = '#' + id;
    if (bool === true) {
        jQuery(jquery_id).removeClass('disabled');
        jQuery(jquery_id).attr('onClick', 'return');
    }
    else {
        jQuery(jquery_id).addClass('disabled');
        jQuery(jquery_id).attr('onClick', 'return false');
    }
};
