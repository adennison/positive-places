if(window.pos === undefined) {
    window.pos = {};
}

if(window.pos.manage_projects === undefined) {
    window.pos.manage_projects = {};
}

jQuery(function(){
    window.pos.manage_projects.load_listeners();
});

// Initialise click handler for 'Delete' link
// Also the handler for 'Cancel' button
window.pos.manage_projects.load_listeners = function(projects_pk_list) {

    jQuery(".project_delete_link").attr('onClick', 'return false');

    var project_input, project_pk, link;
    // Handler for delete link
    jQuery(".project_delete_link").click(function() {
        link = jQuery(this);
        project_input = link.parent('td').find("[name='project_pk']");
        project_pk = project_input.val();
        pos.manage_projects.toggle_confirm_delete_button(project_pk, true);
        link.parent('td').parent('tr').css("background","#F5F5F5"); // Highlight the row
    });
    // Handler for Cancel button
    jQuery(".project_cancel_delete").click(function() {
        var cancel_button = jQuery(this);
        project_input = cancel_button.siblings('input').closest("[name='project_pk']");
        project_pk = project_input.val();
        pos.manage_projects.toggle_confirm_delete_button(project_pk, false);
        link.parent('td').parent('tr').css("background",""); // Unhighlight the row
    })
};

// Toggle the Confirm Delete/Cancel buttons and the initial 'Delete' link
// 'bool' = true hides Delete link and shows the Confirm/Cancel buttons
// 'bool' = false shows the Delete link and hides the Confirm/Cancel buttons
window.pos.manage_projects.toggle_confirm_delete_button = function(project_pk, bool) {
    if (bool === true) {
        jQuery("#id_delete_project_link_"+project_pk).css("display", "none");
        jQuery("#id_submit_delete_button_"+project_pk).css("display", "inline-block");
        jQuery("#id_cancel_delete_button_"+project_pk).css("display", "inline-block");
    } else if (bool == false) {
        jQuery("#id_delete_project_link_"+project_pk).css("display", "inline-block");
        jQuery("#id_submit_delete_button_"+project_pk).css("display", "none");
        jQuery("#id_cancel_delete_button_"+project_pk).css("display", "none");
    }

};
