if(window.pos === undefined) {
    window.pos = {};
}

if(window.pos.user_login === undefined) {
    window.pos.user_login = {};
}


// Open the Login dialog modal
window.pos.user_login.open_modal = function(){

    jQuery("#dialog").css("display", "inline-block");
    jQuery("#dialog").dialog("open");

};


// Run the Login or Close dialog modal functions
window.pos.user_login.create_login_modal = function(){

    // Create some of the dialog elements
    jQuery("#dialog").dialog({
        autoOpen: false,
        resizable: false,
        height: 300,
        width: 520,
        modal: true,
        buttons: [{
            id: "btn_login",
            text: "Log In",
            click: function() {
                jQuery("#id_login_button").click();
            }
        }, {
            id: "btn_cancel",
            text: "Cancel",
            click: function() {
                jQuery(this).dialog("close");
            }
        }]
    });

    // Set a click handler on the Log in / Register link
    jQuery("#opener").click(function() {
        pos.user_login.open_modal();
    });

    // Set an 'Enter key' handler on the modal
    // Highlights the styled button
    // Submits the form to the server
    jQuery("#modal_login").keypress(function(event) {
        if(event.keyCode === 13) {
            event.preventDefault();
            jQuery("#btn_login").addClass("ui-state-hover");
            jQuery("#id_login_button").click();
        }
    });

};

// Set a click handler on the Log in link for password reset page
window.pos.user_login.set_password_reset_login_handler = function() {

    jQuery("#password_reset_login").click(function() {
        pos.user_login.open_modal();
    });

};
