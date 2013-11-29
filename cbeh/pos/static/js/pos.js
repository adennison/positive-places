(function () {
    "use strict";

    if(window.pos === undefined) {
        window.pos = {};
    }

    if(window.pos.map === undefined) {
        window.pos.map = {};
    }

    if(window.address === undefined) {
        window.address = {};
    }

    /*
    Function for Regions map
    Loads Openlayers map with Google base
    Inputs:
            map_elem_id, (map object),      map object in the template
            json_list (list of objects),    holds 'x' nearest POSs in a JSON list
                                            WKT string with lat/address.long values in each list element
                                            JSON list elements to get geometry are called 'pos_wkt'
            lat (float),                    geocoded latitude of the user's searched address
            address.lon (float),            geocoded longitude of the user's searched address
    */
    window.pos.map.create_regions_map = function(map_elem_id, wkt_str, legend_entry, region_type) {
        address.functionCalled = "Region";
        var wgs84 = new OpenLayers.Projection("EPSG:4326");

        // Create style array for the polygon features
        var polygonStyleMap = pos.create_region_style_map(region_type);
        // Create style array for Google Streets base map
        var google_streets_styles = pos.create_google_streets_styles();

        // Create the POS WMS Layers
        var wmsLayers = pos.map.createWMSPOSLayers();

        // Declare Layers
        var polygonVector = new OpenLayers.Layer.Vector(legend_entry, {styleMap: polygonStyleMap});
        var google_street_base = new OpenLayers.Layer.Google("Streets", {numZoomLevels: 20, type: 'styled'});
        var google_hybrid_base = new OpenLayers.Layer.Google("Satellite", {type: google.maps.MapTypeId.HYBRID, numZoomLevels: 20}, {visibility: false});

        var map = new OpenLayers.Map( map_elem_id, {
            controls: [
                new OpenLayers.Control.Navigation(),
                new OpenLayers.Control.ArgParser(),
                new OpenLayers.Control.Attribution(),
                new OpenLayers.Control.Zoom(),
                new OpenLayers.Control.LayerSwitcher(),
                //new OpenLayers.Control.ScaleLine( {topOutUnits: "km", topInUnits: "m", bottomOutUnits: "", bottomInUnits: ""} ),
                new OpenLayers.Control.MousePosition( {displayProjection: wgs84, separator:"&deg;E, ", suffix:"&deg;S" })
            ]
        });

        // Add Google Streets Layer to the map to set the projection of the map view
        map.addLayers([google_street_base]);

        // Apply styled Google Map options
        var styledMapOptions = {name: "Styled Map"};
        var styledMapType = new google.maps.StyledMapType(google_streets_styles, styledMapOptions);
        google_street_base.mapObject.mapTypes.set('styled', styledMapType);
        google_street_base.mapObject.setMapTypeId('styled');

        var displayBounds = new OpenLayers.Bounds(); // Set up map display boundaries

        var polygonGeometry = new OpenLayers.Geometry.fromWKT(wkt_str);
        polygonGeometry.transform(wgs84, map.getProjectionObject()); // make it Google Mercator
        var polygonFeature = new OpenLayers.Feature.Vector(polygonGeometry);
        polygonVector.addFeatures(polygonFeature);

        map.addLayers([google_hybrid_base]);
        // Disable Orthogonal view, i.e. enforce vertical perspective
        google_hybrid_base.mapObject.setTilt(0);
        map.addLayers(wmsLayers);
        map.addLayers([polygonVector]);

        // Zoom to bounds of all Geometries
        displayBounds = polygonGeometry.getBounds();
        map.zoomToExtent(displayBounds, true);
        map.zoomTo(map.getZoomForExtent(displayBounds));

        return map;
    };

    /*
    Function for POS map
    Loads Openlayers map with Google base
    Inputs:
            map_elem_id, (map object),      map object in the template
            json_list (list of objects),    holds 'x' nearest POSs in a JSON list
                                                WKT string with lat/long values in each list element
                                                JSON list elements to get geometry are called 'pos_wkt'
            lat (float),                    geocoded latitude of the user's searched address
            lon (float),                    geocoded longitude of the user's searched address
    */
     // window.pos.map.create_pos_map = function(map_elem_id, json_list, legend_entry) {
    window.pos.map.create_pos_map = function(map_elem_id, json_list, parts_list, types_list, lat, lon, num_parks) {
        if(window.address === undefined) {
                window.address = {};
        }

        // for (var i=0; i<types_list.length; i++) {
        //     console.log(types_list[i]);
        // }

        // for (i=0; i<json_list.length; i++) {
        //     console.log(i);
        //     console.log(json_list[i]);
        // }

        // for (i=0; i<parts_list.length; i++) {
        //     console.log(i);
        //     console.log(parts_list[i]);
        // }

        // Push function arguments into the map object
        address.functionCalled = "POS";
        address.num_parks = num_parks;
        address.types_list = types_list;
        address.lon = lon;
        address.lat = lat;

        // address.functionCalled = "POS";

        var wgs84 = new OpenLayers.Projection("EPSG:4326"); // Define a projection for working with

        // Allow testing of specific renderers via "?renderer=Canvas", etc
        var renderer = OpenLayers.Util.getParameters(location.href).renderer;
        renderer = (renderer) ? [renderer] : OpenLayers.Layer.Vector.prototype.renderers;

        // Create style array (colour, size, etc) for searched address location marker point
        var addressStyleMap = pos.create_marker_park_address_style_map();
        // Create style array for POS polygon features
        window.address.posStyleMap = pos.create_pos_park_style_map();
        // Create a lookup for styling the different POS features (this will extend window.address.posStyleMap)
        window.address.posColourLookup = pos.create_pos_colour_lookup();
        // Create style array for Google Streets base map
        var google_streets_styles = pos.create_google_streets_styles();

        // Set the scale and units to switch from vector POS to WMS POS - minScale for vector and maxScale for WMS
        window.address.scaleSwitch = 100000;
        window.address.scaleUnits = 'm';

        // Create the POS WMS Layers
        var wmsLayers = pos.map.createWMSPOSLayers();

        // Create a vector layer for each pos type description
        var polygonVectorsArr = [];
        for (var i=0; i<address.types_list.length; ++i) {
            polygonVectorsArr[i] = new OpenLayers.Layer.Vector(address.types_list[i].description, {styleMap: address.posStyleMap, minScale: address.scaleSwitch, units: address.scaleUnits});
        }

        window.address.polygonVectorsArr = polygonVectorsArr;

        // Declare Layers
        //window.address.searchedParkVector = new OpenLayers.Layer.Vector(legend_entry, {styleMap: address.posStyleMap});
        window.address.searchPointVector = new OpenLayers.Layer.Vector("Your Location", {styleMap: addressStyleMap, renderers: renderer});
        // window.address.polygonVector = new OpenLayers.Layer.Vector(legend_entry + " - Other", {styleMap: address.posStyleMap});
        var google_street_base = new OpenLayers.Layer.Google("Streets", {numZoomLevels: 20, type: 'styled', "tileOptions": {"crossOriginKeyword": null}});
        var google_hybrid_base = new OpenLayers.Layer.Google("Satellite", {type: google.maps.MapTypeId.HYBRID, numZoomLevels: 20}, {visibility: false});

        var map = new OpenLayers.Map( map_elem_id, {
            controls: [
                new OpenLayers.Control.Navigation(),
                new OpenLayers.Control.ArgParser(),
                new OpenLayers.Control.Attribution(),
                new OpenLayers.Control.Zoom(),
                new OpenLayers.Control.LayerSwitcher(),
                //new OpenLayers.Control.ScaleLine( {topOutUnits: "km", topInUnits: "m", bottomOutUnits: "", bottomInUnits: ""} ),
                new OpenLayers.Control.MousePosition( {displayProjection: wgs84, separator:"&deg;E, ", suffix:"&deg;S" })
            ]
        });

        // Push the layers array into the map object
        if(map.pos === undefined) {
                map.pos = {};
        }

        map.pos.layersWMS = wmsLayers;

        window.pos.map.base_map = map;

        // Add Google Streets Layer to the map to set the projection of the map view
        map.addLayers([google_street_base, google_hybrid_base]);
        // Disable Orthogonal view, i.e. enforce vertical perspective
        google_hybrid_base.mapObject.setTilt(0);

        // Create the Suburb and LGA WMS layers
        var suburbWMSLayer = pos.map.createWMSSuburbLayer();
        var lgaWMSLayer = pos.map.createWMSLGALayer();
        map.addLayers([suburbWMSLayer, lgaWMSLayer]);

        // Apply styled options to Google map layer
        var styledMapOptions = {name: "Styled Map"};
        var styledMapType = new google.maps.StyledMapType(google_streets_styles, styledMapOptions);
        google_street_base.mapObject.mapTypes.set('styled', styledMapType);
        google_street_base.mapObject.setMapTypeId('styled');

        // Call the build vector layers function
        var displayBounds = pos.map.buildPOSVectors(parts_list);

        var pointVector = new OpenLayers.Geometry.Point(address.lon, address.lat);
        pointVector.transform(wgs84, map.getProjectionObject()); // make it Google Mercator

        // Zoom to bounds of all Geometries
        displayBounds.extend(pointVector.getBounds()); // Don't forget to include the search address point location in the map view
        map.zoomToExtent(displayBounds, true);
        map.zoomTo(map.getZoomForExtent(displayBounds));

        // Add the google base layer
        // map.addLayers([google_hybrid_base]);

        // Add the wms layers
        // map.addLayers(wmsLayers);



        // // Make the POS polygon features highlightable with mouseover to show popup information
        // // And if clicked go to POS page
        // var selectCtrl = new OpenLayers.Control.SelectFeature([address.searchedParkVector, address.polygonVector], {
        //     hover: false, // user needs to click the feature
        //     onSelect: pos.onFeatureClickParkPage
        //     }
        // );
        // var highlightCtrl = new OpenLayers.Control.SelectFeature([address.searchedParkVector, address.polygonVector], {
        //     hover: true, // user only needs to hover over the feature, not click
        //     multiple: true,
        //     highlightOnly: true, // do not select features here
        //     renderIntent: "select", // options "default", "temporary" or "select" which will apply the appropriate style
        //     eventListeners: {
        //        featurehighlighted: pos.onFeatureHover,
        //        featureunhighlighted: pos.onFeatureUnhover
        //     }
        // });

        // Make the POS polygon features highlightable with mouseover to show popup information
        // And if clicked go to POS page
        var selectCtrl = new OpenLayers.Control.SelectFeature(polygonVectorsArr, {
            hover: false, // user needs to click the feature
            onSelect: pos.onFeatureClickParkPage
            }
        );
        var highlightCtrl = new OpenLayers.Control.SelectFeature(polygonVectorsArr, {
            hover: true, // user only needs to hover over the feature, not click
            highlightOnly: true, // do not select features here
            renderIntent: "select", // options "default", "temporary" or "select" which will apply the appropriate style
            eventListeners: {
               featurehighlighted: pos.onFeatureHover,
               featureunhighlighted: pos.onFeatureUnhover
            }
        });

        // Allow dragging of map when mouse is over polygons
        highlightCtrl.handlers.feature.stopDown = false;
        selectCtrl.handlers.feature.stopDown = false;

        map.addControl(highlightCtrl);
        highlightCtrl.activate();
        map.addControl(selectCtrl);
        selectCtrl.activate();

        pos.highlight_ctrl = highlightCtrl;
        pos.select_ctrl = selectCtrl;

        // Add listeners for map zoom events
        map.events.register('movestart', map, pos.map.onMoveStart);
        map.events.register('moveend', map, pos.map.onMoveEnd);
        map.events.register('zoomend', map, pos.map.onZoomMap);

        return map;
    };

    /*
    Function for Address search results map page
    Loads Openlayers map with Google base
    Inputs:
            map_elem_id, (map object),      map object in the template
            json_list (list of objects),    holds 'x' nearest POSs in a JSON list
                                                WKT string with lat/long values in each list element
                                                JSON list elements to get geometry are called 'pos_wkt'
            types_list (list of objects),   holds the unique pos type for each polygon layer to create
                                                JSON list elements to get the type is called 'description'
            lat (float),                    geocoded latitude of the user's searched address
            lon (float),                    geocoded longitude of the user's searched address
    */
    window.pos.map.create_address_map = function(map_elem_id, json_list, types_list, lat, lon, num_parks) {
        if(window.address === undefined) {
                window.address = {};
        }

        // for (i=0; i<json_list.length; i++) {
        //     console.log(i);
        //     console.log(json_list[i]);
        // }

        // Push function arguments into the map object
        address.functionCalled = "Address";
        address.num_parks = num_parks;
        address.types_list = types_list;
        address.lon = lon;
        address.lat = lat;

        var wgs84 = new OpenLayers.Projection("EPSG:4326");

        // Allow testing of specific renderers via "?renderer=Canvas", etc
        var renderer = OpenLayers.Util.getParameters(location.href).renderer;
        renderer = (renderer) ? [renderer] : OpenLayers.Layer.Vector.prototype.renderers;

        // Create style array (colour, size, etc) for searched address location marker point
        var addressStyleMap = pos.create_marker_address_style_map();
        // Create style array for POS polygon features
        window.address.posStyleMap = pos.create_pos_address_style_map();
        // Create a lookup for styling the different POS features (this will extend address.posStyleMap)
        window.address.posColourLookup = pos.create_pos_colour_lookup();
        // Create style array for Google Streets base map
        var google_streets_styles = pos.create_google_streets_styles();

        // Set the scale and units to switch from vector POS to WMS POS - minScale for vector and maxScale for WMS
        window.address.scaleSwitch = 100000;
        window.address.scaleUnits = 'm';

        // Create the POS WMS Layers
        var wmsLayers = pos.map.createWMSPOSLayers();

        // Create a vector layer for each pos type description
        var polygonVectorsArr = [];
        for (var i=0; i<address.types_list.length; ++i) {
            polygonVectorsArr[i] = new OpenLayers.Layer.Vector(address.types_list[i].description, {styleMap: address.posStyleMap, minScale: address.scaleSwitch, units: address.scaleUnits});
        }

        window.address.polygonVectorsArr = polygonVectorsArr;

        window.address.searchPointVector = new OpenLayers.Layer.Vector('Your Location', {styleMap: addressStyleMap, renderers: renderer});
        var google_street_base = new OpenLayers.Layer.Google("Streets", {numZoomLevels: 20, type: 'styled'});
        var google_hybrid_base = new OpenLayers.Layer.Google("Satellite", {type: google.maps.MapTypeId.HYBRID, numZoomLevels: 20, visibility: true});
        //vlayer = new OpenLayers.Layer.Vector( "Editable" );

        var map = new OpenLayers.Map( map_elem_id, {
            controls: [
                //new OpenLayers.Control.DragFeature(address.searchPointVector),
                new OpenLayers.Control.Navigation(),
                new OpenLayers.Control.ArgParser(),
                new OpenLayers.Control.Attribution(),
                new OpenLayers.Control.Zoom(),
                new OpenLayers.Control.LayerSwitcher(),
                //new OpenLayers.Control.ScaleLine( {topOutUnits: "km", topInUnits: "m", bottomOutUnits: "", bottomInUnits: ""} ),
                //new OpenLayers.Control.Scale(),
                new OpenLayers.Control.MousePosition( {displayProjection: wgs84, separator:"&deg;E, ", suffix:"&deg;S" })
            ]
        });

        window.pos.map.base_map = map;

        //map.addControl(new OpenLayers.Control.EditingToolbar(vlayer));

        // Add Google Streets Layer to the map to set the projection of the map view
        map.addLayers([google_street_base, google_hybrid_base]);
        // Disable Orthogonal view, i.e. enforce vertical perspective
        google_hybrid_base.mapObject.setTilt(0);

        // Create the Suburb and LGA WMS layers
        var suburbWMSLayer = pos.map.createWMSSuburbLayer();
        var lgaWMSLayer = pos.map.createWMSLGALayer();
        map.addLayers([suburbWMSLayer, lgaWMSLayer]);

        // Push the WMS layers array into the map object
        if(map.pos === undefined) {
                map.pos = {};
        }

        map.pos.layersWMS = wmsLayers;

        // Apply styled Google Map options to the base layer
        var styledMapOptions = {name: "Styled Map"};
        var styledMapType = new google.maps.StyledMapType(google_streets_styles, styledMapOptions);
        google_street_base.mapObject.mapTypes.set('styled', styledMapType);
        google_street_base.mapObject.setMapTypeId('styled');

        // Build the vector layers from the json_list array
        var displayBounds = pos.map.buildAddressVectors(json_list);

        var pointVector = new OpenLayers.Geometry.Point(address.lon, address.lat);
        pointVector.transform(wgs84, map.getProjectionObject()); // make it Google Mercator

        // Zoom to bounds of all Geometries
        displayBounds.extend(pointVector.getBounds()); // Don't forget to include the search address point location in the map view
        map.zoomToExtent(displayBounds, true);
        map.zoomTo(map.getZoomForExtent(displayBounds));

        //map.zoomToExtent(searchLocation.getBounds(), true);
        //map.setCenter(new OpenLayers.lonLat(address.lon, address.lat).transform(wgs84, map.getProjectionObject()), zoom);

        // Make the POS polygon features highlightable with mouseover to show popup information
        // And if clicked go to POS page
        var selectCtrl = new OpenLayers.Control.SelectFeature(polygonVectorsArr, {
            hover: false, // user needs to click the feature
            onSelect: pos.onFeatureClick
            }
        );
        var highlightCtrl = new OpenLayers.Control.SelectFeature(polygonVectorsArr, {
            hover: true, // user only needs to hover over the feature, not click
            highlightOnly: true, // do not select features here
            renderIntent: "select", // options "default", "temporary" or "select" which will apply the appropriate style
            eventListeners: {
               featurehighlighted: pos.onFeatureHover,
               featureunhighlighted: pos.onFeatureUnhover
            }
        });
        // Allow dragging of map when mouse is over polygons
        highlightCtrl.handlers.feature.stopDown = false;
        selectCtrl.handlers.feature.stopDown = false;

        map.addControl(highlightCtrl);
        highlightCtrl.activate();
        map.addControl(selectCtrl);
        selectCtrl.activate();

        // Add a drag feature control to move the marker location around
        var dragFeature = new OpenLayers.Control.DragFeature(polygonVectorsArr[address.types_list.length], {
            onComplete: pos.reverse_geocode_lat_long
        }
        );
        map.addControl(dragFeature);
        dragFeature.activate();

        // Add listeners for map zoom events
        map.events.register('movestart', map, pos.map.onMoveStart);
        map.events.register('moveend', map, pos.map.onMoveEnd);
        map.events.register('zoomend', map, pos.map.onZoomMap);

        pos.highlight_ctrl = highlightCtrl;
        pos.select_ctrl = selectCtrl;
        return map;
    };

/*
    Function to get the Upload User Region map elements page working
*/
    window.pos.map.create_upload_user_region_map = function(map_elem_id, wkt_str, user_region_pk) {

        // Set up the map base and some map elements
        var map = pos.map.create_user_region_map(map_elem_id, wkt_str, user_region_pk);

        // Set the View Stats and Scenario Calculator to disabled if no WKT
        // (i.e. no feature exists yet and therefore no stats calculated yet)
        if (wkt_str === 'false') {
            pos.toggle_bootstrap_anchor_button('view_stats_button', false);
            pos.toggle_bootstrap_anchor_button('scenario_calculator_button', false);
        }

        // Set listeners for when the upload button is clicked
        jQuery("#upload_button").click(pos.display_upload_progress);
        jQuery("#upload_button").click(pos.disable_stats_buttons);
    };

/*
    Function to get the Draw User Region map elements page working
*/
    window.pos.map.create_draw_user_region_map = function(map_elem_id, wkt_str, user_region_pk) {

        // Set the View Stats and Scenario Calculator to disabled if no WKT
        // (i.e. no feature exists yet and therefore no stats calculated yet)
        if (wkt_str === 'false') {
            pos.toggle_bootstrap_anchor_button('view_stats_button', false);
            pos.toggle_bootstrap_anchor_button('scenario_calculator_button', false);
        // // The element holding the Wkt has data in it
        // } else if (jQuery("#id_region_wkt").val('false') === false) {

        }
        window.pos.wkt_str = wkt_str;

        // Set up the map base and some map elements
        var map = pos.map.create_user_region_map(map_elem_id, wkt_str, user_region_pk);

        var editLayer = window.pos.editLayer;

        // Create map controls
        var draw_feature_control = new OpenLayers.Control.DrawFeature(
            editLayer,
            OpenLayers.Handler.Polygon,
            {
                title:'Draw a region polygon',
                type: OpenLayers.Control.TYPE_TOGGLE,
                eventListeners: {
                    'activate': pos.toggle_drawing_controls,
                    'deactivate': draw_original_feature
                }
            }
        );
        var modify_feature_control = new OpenLayers.Control.ModifyFeature(
            editLayer,
            {
                title:'Modify a region polygon',
                type: OpenLayers.Control.TYPE_TOGGLE,
                eventListeners: {
                    'activate': pos.toggle_drawing_controls,
                    'deactivate': draw_original_feature
                }
            }
        );
        var panel = new OpenLayers.Control.Panel(/*{defaultControl: draw_feature_control}*/);
        panel.addControls([draw_feature_control, modify_feature_control]);

        // Add map controls
        map.addControl(panel);
        panel.deactivate(); // user needs to click the edit button first

        // Add a listener to insert the new/modified geometry into the database
        editLayer.events.on({
            "featureselected": function(feature) {
                window.pos.original_feature = editLayer.features[0].clone(); // to draw it back later if cancel drawing
                //window.pos.first_feature = editLayer.features[0].clone(); // to draw it back later if cancel drawing
            },
            // "afterfeaturemodified": insertRecord,
            // "featureadded": insertRecord
            "afterfeaturemodified": pos.set_feature_complete,
            "featureadded": pos.set_feature_complete,
            "featureremoved": pos.set_feature_cannot_save,
            "featuremodified": pos.set_feature_cannot_save,
            "beforefeaturemodified": pos.set_feature_cannot_save // after the select but before modify
        });

        // Add a callback to remove all features from the temp layer if a new feature is created
        // i.e. there should only ever be 1 feature in this layer
        // Also store the original polygon feature
        draw_feature_control.handler.callbacks.point = function(data) {
            if(editLayer.features.length > 0) {
                if (window.pos.first_feature) {
                    window.pos.original_feature = window.pos.first_feature.clone();//editLayer.features[0].clone(); // to draw it back later if cancel drawing
                    //window.pos.first_feature = editLayer.features[0].clone();
                }
                editLayer.removeAllFeatures();
            }
        };

        // On user deactivate their draw/modify control, redraw the original region back to the map
        function draw_original_feature(event) {
            pos.redraw_original_region(editLayer, window.pos.original_feature);
            window.pos.feature_may_be_saved = true;
            //window.pos.feature_completed = false;
        }

        // On user click the Create/Edit button, activate the panel
        jQuery("#edit_button").click(toggle_panel);
        // Toggle the panel active/deactive
        // Also deals with saving/cancelling polygons
        function toggle_panel() {
            map = window.pos.map.base_map;
            // Check if the panel is in the map's controls
            var panelControlList = map.getControlsByClass("OpenLayers.Control.Panel");
            // Panel not activated yet, add it
            if (panelControlList[0].active === false) {
                panel.activate();
                jQuery("#edit_button").val('Cancel');
                jQuery("#save_button").css("display", "inline-block");
                // Disable the stats buttons
                pos.toggle_bootstrap_anchor_button('view_stats_button', false);
                pos.toggle_bootstrap_anchor_button('scenario_calculator_button', false);
                // // Disable the upload file button
                // jQuery("#upload_button").prop('disabled', true);
                // jQuery("#region_upload_button").prop('disabled', true);
                // Flash the drawing controls
                pos.flash_drawing_controls();
            } else {
                panel.deactivate();
                jQuery("#edit_button").val('Create/Edit Region');
                jQuery("#save_button").css("display", "none");
                window.pos.feature_completed = false;
                // // Enable the upload file button
                // jQuery("#upload_button").prop('disabled', false);
                // jQuery("#region_upload_button").prop('disabled', false);
                // Draw original feature if it existed
                if (window.pos.feature_saved === false) {
                    pos.redraw_original_region(editLayer, window.pos.first_feature);
                    // Remove the 1st drawn, unsaved feature on Cancel
                    if (window.pos.first_feature === undefined) {
                        editLayer.removeAllFeatures();
                    }
                } else {
                    window.pos.feature_redraw = false;
                }
                // Allow user to access stats data
                if (window.pos.wkt_str !== 'false') {
                    pos.toggle_bootstrap_anchor_button('view_stats_button', true);
                    pos.toggle_bootstrap_anchor_button('scenario_calculator_button', true);
                }
            }
        }

        // On user click the Save button, attempt to save the geometry
        jQuery("#save_button").click(save_geometry);
        function save_geometry() {
            pos.display_upload_progress();
            var map = window.pos.map.base_map;
            var layer = map.getLayersByName('Editable')[0];
            var feature = layer.features[0];
            if (feature === null || feature === undefined) {
                jQuery.jGrowl("You need to draw a region first.", {
                    header: 'Warning',
                    position: 'top-right',
                    sticky: false,
                    life: 5000
                });
                pos.hide_upload_progress();
            } else if (window.pos.feature_may_be_saved === false) {
                jQuery.jGrowl("You need to complete the drawing first.", {
                    header: 'Warning',
                    position: 'top-right',
                    sticky: false,
                    life: 5000
                });
                pos.hide_upload_progress();
            } else if (window.pos.feature_completed === false) {
                jQuery.jGrowl("You need to complete the drawing first.", {
                    header: 'Warning',
                    position: 'top-right',
                    sticky: false,
                    life: 5000
                });
                pos.hide_upload_progress();
            } else {
                pos.toggle_bootstrap_anchor_button('manage_projects_button', false);
                pos.insert_record(feature);
                window.pos.feature_completed = false;
                // Disable the Cancel/Save buttons so user can't press until the
                // processing is all finished
                jQuery("#edit_button").prop('disabled', true);
                jQuery("#save_button").prop('disabled', true);
                // Deactivate the drawing buttons
                pos.deactivate_drawing_controls();
                window.pos.feature_saved = true;
            }
        }
    };

/*
    Function to create and display the User Region map page base elements
    Loads Openlayers map with Google base
*/
    window.pos.map.create_user_region_map = function(map_elem_id, wkt_str, user_region_pk) {
        if(window.address === undefined) {
            window.address = {};
        }

        address.functionCalled = "Region";

        // Set the projection for the coordinates, user click will return Google Mercator -- need to transform below
        var wgs84 = new OpenLayers.Projection("EPSG:4326");

        window.pos.map.user_region_pk = user_region_pk;

        // Create style array for the polygon features
        var polygonStyleMap = pos.create_user_region_style_map();
        // Create style array for Google Streets base map
        var google_streets_styles = pos.create_google_streets_styles();

        // Create map layers
        // window.address.polygonVector = new OpenLayers.Layer.Vector("Other Parts", {styleMap: address.posStyleMap});
        var editLayer = new OpenLayers.Layer.Vector( "Editable", {displayInLayerSwitcher: false, styleMap: polygonStyleMap});
        var google_street_base = new OpenLayers.Layer.Google("Streets", {numZoomLevels: 20, type: 'styled'});
        var google_hybrid_base = new OpenLayers.Layer.Google("Satellite", {type: google.maps.MapTypeId.HYBRID, numZoomLevels: 20, visibility: true});

        // Create map
        var map = new OpenLayers.Map(map_elem_id, {
            controls: [
                new OpenLayers.Control.Navigation(),
                new OpenLayers.Control.Zoom(),
                new OpenLayers.Control.LayerSwitcher()
            ]
        });

        // Add Google Streets Layer to the map to set the projection of the map view
        map.addLayers([google_street_base]);
        map.addLayers([google_hybrid_base]);
        // Disable Orthogonal view, i.e. enforce vertical perspective
        google_hybrid_base.mapObject.setTilt(0);
        // Create the POS WMS Layers
        var wmsLayers = pos.map.createWMSPOSLayers();
        map.addLayers(wmsLayers);

        map.addLayers([editLayer]);

        // Apply styled options to Google map layer
        var styledMapOptions = {name: "Styled Map"};
        var styledMapType = new google.maps.StyledMapType(google_streets_styles, styledMapOptions);
        google_street_base.mapObject.mapTypes.set('styled', styledMapType);
        google_street_base.mapObject.setMapTypeId('styled');

        // Add the polygon if it exists
        if(wkt_str !== 'false') {
            var polygonGeometry = new OpenLayers.Geometry.fromWKT(wkt_str);
            polygonGeometry.transform(wgs84, map.getProjectionObject()); // make it Google Mercator
            var polygonFeature = new OpenLayers.Feature.Vector(polygonGeometry);
            editLayer.addFeatures(polygonFeature);
            window.pos.first_feature = editLayer.features[0].clone();
            // Zoom to bounds of all Geometries
            var displayBounds = polygonGeometry.getBounds();
            map.zoomToExtent(displayBounds, true);
            map.zoomTo(map.getZoomForExtent(displayBounds));
        } else {
            // Zoom the map to Perth Metro
            map.setCenter(new OpenLayers.LonLat(115.8, -32).transform(
                wgs84,
                map.getProjectionObject()
            ), 10);
        }

        window.pos.map.base_map = map;
        window.pos.feature_completed = false;
        window.pos.editLayer = editLayer;
        return map;
    };

    // When user clicks 'Save Region' button, send the geometry to the server
    // and save in database
    window.pos.insert_record = function(feature) {

        // Transform the geometry to WGS84 to get a WKT to send to server
        // Clone the geometry so we do not transform the on-screen features
        var polyGeometry = feature.geometry.clone();
        var wgs84 = new OpenLayers.Projection("EPSG:4326");
        var googleMercator = new OpenLayers.Projection("EPSG:900913");
        polyGeometry.transform(googleMercator, wgs84);
        var polygonFeature = new OpenLayers.Feature.Vector(polyGeometry);
        var polygonWkt = new OpenLayers.Format.WKT().write(polygonFeature);

        // Get the PK of the user region
        var user_region_pk = window.pos.map.user_region_pk;

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
                wkt: polygonWkt,
                user_region_pk: user_region_pk
            }
        });

        request.done(function (json_list) {
            // Check if there is any problem with saving the polygon
            // Alert the message to the user
            if (json_list.issue) {
                //alert(json_list.message);
                jQuery.jGrowl(json_list.message, {
                    header: 'Warning',
                    position: 'top-right',
                    sticky: false,
                    life: 10000
                });
                window.pos.feature_completed = false;
                window.pos.first_feature = window.pos.editLayer.features[0].clone();

            } else {
                window.pos.first_feature = window.pos.editLayer.features[0].clone();
                jQuery.jGrowl("Your region has been saved!", {
                    header: 'Success',
                    position: 'top-right',
                    //group: 'div.jGrowl div.jGrowl-notification.pos_success',
                    //theme:'div.jGrowl div.jGrowl-notification.pos_success',
                    sticky: true
                });
                // Switch the Edit/Save buttons off
                jQuery("#edit_button").val('Create/Edit Region');
                jQuery("#save_button").css("display", "none");
                // Deactivate the drawing panel
                var map = window.pos.map.base_map;
                var panel = map.getControlsByClass("OpenLayers.Control.Panel")[0];
                panel.deactivate();
                // Allow user to access stats data
                pos.toggle_bootstrap_anchor_button('view_stats_button', true);
                pos.toggle_bootstrap_anchor_button('scenario_calculator_button', true);
                // Set a toggle, page to be refreshed if user navigates elsewhere
                // and then hits the browser's 'Back' button
                jQuery("#refreshed").val('yes');
            }
            // Hide the upload progress display
            jQuery('#progress_display').css("display", "none");
            jQuery('#upload_text').css("display", "none");
            // Enable the Cancel/Save buttons so user can press them again
            // the next time they are displayed
            jQuery("#edit_button").prop('disabled', false);
            jQuery("#save_button").prop('disabled', false);
            pos.toggle_bootstrap_anchor_button('manage_projects_button', true);
        });
    };

    // Disable View Stats, Scenario Calculator & Manage Projects buttons
    // While a shapefile is being uploaded
    window.pos.disable_stats_buttons = function() {
        pos.toggle_bootstrap_anchor_button('view_stats_button', false);
        pos.toggle_bootstrap_anchor_button('scenario_calculator_button', false);
        pos.toggle_bootstrap_anchor_button('manage_projects_button', false);
    };

    // Enable/Disable a bootstrap 'href' button by its ID.
    // 'bool' input: true if enabling, false if disabling
    window.pos.toggle_bootstrap_anchor_button = function(id, bool) {
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

    // Standard notification growl popup
    // Only used after user tries to upload a region shapefile
    window.pos.show_growl = function(message) {
        jQuery.jGrowl(message, {
            position: 'top-right',
            sticky: true
        });
    };

    // On submit button display the upload progress info to the user
    window.pos.display_upload_progress = function(event) {
        jQuery('#progress_display').css("display", "inline-block");
        jQuery('#upload_text').css("display", "inline-block");
    };

    // Hide upload progress from the user
    // After bad user upload attempt or finish copying user stats from LGA/Suburb
    window.pos.hide_upload_progress = function(event) {
        jQuery('#progress_display').css("display", "none");
        jQuery('#upload_text').css("display", "none");
    };

    // If user drawing/modification is complete, set some values
    window.pos.set_feature_complete = function(feature) {
        window.pos.feature_completed = true;
        window.pos.original_feature = undefined;
        window.pos.feature_may_be_saved = true;
        window.pos.feature_saved = false;
    };

    // If user drawing/modification is in process, set to false
    window.pos.set_feature_cannot_save = function(feature) {
        window.pos.feature_may_be_saved = false;
    };

    // Toggles on/off the draw/modify controls
    // If one is clicked and hence activated, the other is deactivated
    // Also redraw any existing features on cancel
    window.pos.toggle_drawing_controls = function(event) {

        var currentControl = event.object;
        var map = window.pos.map.base_map;
        var editLayer = window.pos.editLayer;
        var original_feature;
        if (original_feature !== undefined) {
            original_feature = window.pos.original_feature.clone();
        }
        var panelList = map.getControlsByClass("OpenLayers.Control.Panel");

        for (var i=0, pLen=panelList.length; i<pLen; i++) {
            var currPanel = panelList[i];
            for (var j=0, len=currPanel.controls.length; j<len; j++) {
                if (currPanel.controls[j] !== currentControl) {
                    if (currPanel.controls[j].active) {
                        currPanel.controls[j].deactivate();
                    }
                }
            }
        }
        // Redraw the original feature if necessary
        pos.redraw_original_region(editLayer, original_feature);
    };

    // Deactivate any active drawing controls (i.e. both draw and modify icons)
    // Only happens after a successful save to the database
    window.pos.deactivate_drawing_controls = function() {
        var map = window.pos.map.base_map;
        var panelList = map.getControlsByClass("OpenLayers.Control.Panel");

        for (var i=0, pLen=panelList.length; i<pLen; i++) {
            var currPanel = panelList[i];
            for (var j=0, len=currPanel.controls.length; j<len; j++) {
                if (currPanel.controls[j].active) {
                    currPanel.controls[j].deactivate();
                }
            }
        }
    };

    // Flash the drawing controls
    window.pos.flash_drawing_controls = function() {
        var map = window.pos.map.base_map;
        var drawControl = map.getControlsByClass("OpenLayers.Control.DrawFeature")[0];
        var modifyControl = map.getControlsByClass("OpenLayers.Control.ModifyFeature")[0];

        modifyControl.activate();
        setTimeout(function() {
            modifyControl.deactivate();
            drawControl.activate();
        }, 150);
        setTimeout(function() { drawControl.deactivate(); }, 300);
    };

    // Redraw any original feature back to the map
    window.pos.redraw_original_region = function(editLayer, original_feature) {
        // Redraw the original feature if it's gone and another feature has not been created
        if (editLayer.features.length === 0 && original_feature !== undefined) {
            editLayer.addFeatures(original_feature);
        } else if (window.pos.feature_completed === false && original_feature !== undefined) {
            editLayer.removeAllFeatures();
            editLayer.addFeatures(original_feature);
            window.pos.first_feature = original_feature.clone();
            window.pos.feature_completed = false;
            window.pos.feature_may_be_saved = true;
        }
    };

    // Highlight a park in the map when the user hovers over it in the table
    // Input is the primary Key for the park in question
    // (PK is extracted in the HTML template from the id tag of the table row)
    window.pos.highlightFeatureFromTable = function(pos_pk) {
        var map = pos.map.base_map; // Get the map viewport
        var highlightCtrl = pos.highlight_ctrl; // Get the highlight control activated for the map
        pos_pk = parseInt(pos_pk);

        for (var i=0; i<map.layers.length; ++i) {
            if (map.layers[i].features) { // if there are features, i.e. it's a vector layer
                for (var j=0; j<map.layers[i].features.length; ++j) { // cycle through features
                    if (map.layers[i].features[j].attributes.pos_pk === pos_pk) {
                        highlightCtrl.select(map.layers[i].features[j]);
                        //console.log("Match, PK " + map.layers[i].features[j].attributes.pos_pk + ", type " + map.layers[i].features[j].attributes.pos_type_c);
                        //console.log(map.layers[i].features[j]);
                    }
                }
            }
        }
    };

    // Unhighlight any parks that are showing in the map view
    // Called from HTML template when user moves mouse away from a selected park polygon / table row
    window.pos.unHighlightAllFeatures = function() {
        var map = pos.map.base_map; // Get the map viewport
        var highlightCtrl = pos.highlight_ctrl; // Get the highlight control activated for the map

        highlightCtrl.unselectAll(); // Unselect all parks
    };

    // Create a popup for a feature
    window.pos.createPopup = function(popupID, popupText, feature) {
        var map = pos.map.base_map; // Get the map viewport
        var popup = new OpenLayers.Popup(popupID, // ID for popup
            feature.geometry.getBounds().getCenterLonLat(), // Centre of popup long/lat
            null, // size of the content in the popup
            "<div style='color:#77933C'>" + popupText + "</div>", // HTML string to display in popup
            false, // show X in top right corner of popup to close it (true/false)
            null); // function call if close popup is true
        //popup.backgroundColor = "transparent";
        popup.backgroundColor = "#FFFFF0";
        popup.border = "1px solid gray";
        //popup.panMapIfOutOfView = true;
        popup.autoSize = true;
        popup.disableFirefoxOverflowHack = true; // prevent redrawing all elements in Firefox
        feature.popup = popup;

        jQuery(popup.contentDiv).mouseleave(function(event) {
            //feature.layer.map.removePopup(popup);
            for (var i=0; i<map.popups.length; ++i) {
                    map.removePopup(map.popups[i]);
                }

            pos.highlight_ctrl.unselect(feature);
        });
    };

    window.pos.onFeatureClick = function(feature) {
        // Only load if user clicked on a Park polygon
        if (feature.attributes.pos_type_c === "Park") {
            window.location.pathname = "/cbeh/pos/pos/" + feature.attributes.pos_pk;
            //window.location = "../pos/" + feature.attributes.pos_pk; //    "../"   ---> go up one path
        }
        // Otherwise remove the selection and turn on the highlight
        else {
            pos.select_ctrl.unselect(feature);
            pos.highlight_ctrl.select(feature);
        }
    };

    window.pos.onFeatureClickParkPage = function(feature) {
        var loadedParkPk = parseInt(location.pathname.slice(14,-1), 10);
        var clickedParkPk = feature.attributes.pos_pk;
        // Load page for clicked Park polygon if it is not the currently loaded Park
        if (clickedParkPk !== loadedParkPk && feature.attributes.pos_type_c === "Park") {
            window.location.pathname = "/cbeh/pos/pos/" + feature.attributes.pos_pk;
            // window.location = "../" + feature.attributes.pos_pk; //    "../"   ---> go up one path
        }
        else {
            // Do not reload this park, but remove selection and re-enable hover control
            // ( Workaround for OpenLayers bug )
            pos.select_ctrl.unselect(feature);
            pos.highlight_ctrl.select(feature);
            //feature.layer.map.removePopup(feature.popup);
        }
    };

    window.pos.onFeatureHover = function(event) {
        // Note that the feature may be the searched address point and therefore will not
        // have a popup set.
        // https://github.com/openlayers/openlayers/issues/521
        var feature = event.feature;
        var popup = feature.popup;
        jQuery("#"+feature.attributes.pos_pk).css("background","#F0FFF0"); // highlight the table row
        if(popup !== undefined && popup !== null) {
            feature.layer.map.addPopup(popup);
            //jQuery("#"+feature.attributes.pos_pk).css("background","#F0FFF0"); // highlight the table row
        }
    };

    window.pos.onFeatureUnhover = function(event) {
        // Note that the feature may be the searched address point and therefore will not
        // have a popup set.
        // https://github.com/openlayers/openlayers/issues/521
        var map = pos.map.base_map;
        var feature = event.feature;
        var popup = event.feature.popup;

    //    console.log(popup.contentDiv);
    //    console.log(feature.layer.div);
        jQuery("#"+feature.attributes.pos_pk).css("background",""); // unhighlight the table row
        if(popup !== undefined && popup !== null) {
            // Workarounds so popup box does not flicker
            var is_popup_hover = jQuery(popup.contentDiv).is(":hover");
            if(is_popup_hover) {
                pos.highlight_ctrl.select(feature);
                jQuery("#"+feature.attributes.pos_pk).css("background","#F0FFF0"); // highlight the table row
            }
            else {
                //feature.layer.map.removePopup(popup);
                for (var i=0; i<map.popups.length; ++i) {
                    map.removePopup(map.popups[i]);
                }
                jQuery("#"+feature.attributes.pos_pk).css("background",""); // unhighlight the table row
            }
        }
        //feature.popup.destroy();
        //feature.popup = null;
    };

    // When user drags address marker to another location event, get lat/long coordinates of new location
    // Reverse geocode the latitude, longitude coordinate pair into a textual address description
    // And then load the information into nearest address search results page
    // Uses Google API
    window.pos.reverse_geocode_lat_long = function(event) {

        // Set the projection for the coordinates, user click will return Google Mercator -- need to transform below
        var wgs84 = new OpenLayers.Projection("EPSG:4326");

        // Get the map viewport
        var map = pos.map.base_map;

        // Get the coordinates of new marker location
        var markerlonLat = event.geometry.getBounds().getCenterLonLat();
        markerlonLat.transform(map.getProjectionObject(), wgs84); // transform from Google Mercator to WGS84
        var lat_wgs84 = markerlonLat.lat;
        var long_wgs84 = markerlonLat.lon;
        //alert("You dragged the marker to " + lat_wgs84 + " S, " + address.long_wgs84 + " E");

        // Make variables for a Google lat/address.long point, and a Google geocoder object
        var google_latlong = new google.maps.LatLng(lat_wgs84, long_wgs84);
        var geocoder = new google.maps.Geocoder();
        // Reverse Geocode the corrdinates into a text address
        geocoder.geocode({'latLng': google_latlong}, function(results, status) {
            if (status === google.maps.GeocoderStatus.OK) {
                if (results[1]) {
                    address = results[0].formatted_address;
                    //alert("You dragged the marker to " + address);
                    // Give the information to search.py to reload the page with new results
                    //var csrfToken = jQuery('[name="csrfmiddlewaretoken"]').val(); // get the CSRF Token - security
                    var urlParameters = {
                        geocodeLocation: address,
                        latitude: lat_wgs84,
                        longitude: long_wgs84
                        //csrfmiddlewaretoken: csrfToken
                    };
                    location.search = jQuery.param(urlParameters);
                } else {
                  alert('No results found');
                }
            } else {
                alert('Geocoder failed due to: ' + status);
            }
        });
    };

    // Create style mapping for the address marker
    window.pos.create_marker_address_style_map = function() {
        // Marker shape setup
        var shadow_z_index = 10;
        var marker_z_index = 11;
        //var diameter = 200;

        var addressStyleMap = new OpenLayers.StyleMap({
            // Set the external graphic and background images
            externalGraphic: "../../../static/images/marker.png",
            backgroundGraphic: "../../../static/images/marker_shadow.png",
            // Offset the graphic so the bottom point of the marker is on the location
            graphicYOffset: -21,
            // Make sure the background shadow graphic is positioned correctly relative to the external graphic
            backgroundXOffset: 0,
            backgroundYOffset: -20,
            // Set the z-indexes of both graphics to make sure the background
            // graphic stays in the background (shadow under marker)
            graphicZIndex: marker_z_index,
            backgroundGraphicZIndex: shadow_z_index,
            // Set the size of the marker graphics on the map
            pointRadius: 14
        });
        return addressStyleMap;
    };

    // Create style mapping for the address marker
    window.pos.create_marker_park_address_style_map = function() {
        // Marker shape setup
        var shadow_z_index = 10;
        var marker_z_index = 11;
        //var diameter = 200;

        var addressStyleMap = new OpenLayers.StyleMap({
            // Set the external graphic and background images
            externalGraphic: "../../../../static/images/marker.png",
            backgroundGraphic: "../../../../static/images/marker_shadow.png",
            // Offset the graphic so the bottom point of the marker is on the location
            graphicYOffset: -21,
            // Make sure the background shadow graphic is positioned correctly relative to the external graphic
            backgroundXOffset: 0,
            backgroundYOffset: -20,
            // Set the z-indexes of both graphics to make sure the background
            // graphic stays in the background (shadow under marker)
            graphicZIndex: marker_z_index,
            backgroundGraphicZIndex: shadow_z_index,
            // Set the size of the marker graphics on the map
            pointRadius: 14
        });
        return addressStyleMap;
    };

    // Create default style mapping for POSs on the address search page
    window.pos.create_pos_address_style_map = function() {
        address.posStyleMap = new OpenLayers.StyleMap({
            "default": new OpenLayers.Style({
                fillOpacity: 0.5,
                strokeWidth: 1,
                pointRadius: 5,
                label: "${park_name}",
                labelAlign: "cm",
                fontColor: "green",
                fontSize: "10px",
                fontFamily: "Arial",
                fontWeight: "bold",
                labelOutlineColor: "green",
                labelOutlineWidth: 0.00001
            }),
            "select": new OpenLayers.Style({
                //fillOpacity: 0.2,
                strokeWidth: 2,
                //pointRadius: 5
                label: "${park_name}",
                labelAlign: "cm",
                fontColor: "green",
                fontSize: "10px",
                fontFamily: "Arial",
                fontWeight: "bold",
                labelOutlineColor: "#FFFFF0",
                labelOutlineWidth: 3
            })
        });
        return address.posStyleMap;
    };

    // Create default style mapping for POSs on the Park page
    window.pos.create_pos_park_style_map = function() {
        var posStyleMap = new OpenLayers.StyleMap({
            "default": new OpenLayers.Style({
                fillOpacity: 0.5,
                strokeWidth: 1,
                pointRadius: 5
            }),
            "select": new OpenLayers.Style({
                //fillOpacity: 0.2,
                strokeWidth: 2
                //pointRadius: 5
            })
        });
        return posStyleMap;
    };

    // Create default style mapping for Suburb / LGA on the Regions page
    window.pos.create_region_style_map = function(regionType) {
        var polygonColour;

        if (regionType === 'SUB') {
            polygonColour = '#FF6C5B';
        } else if (regionType === 'LGA') {
            polygonColour = '#44D2CD';
        } else if (regionType === 'USER') {
            polygonColour = '#BB8CF7';
        } else if (regionType === 'SP') {
            polygonColour = '#BB8CF7';
        } else {
            polygonColour = 'grey';
        }

        var regionStyleMap = new OpenLayers.StyleMap(OpenLayers.Util.applyDefaults(
            {
                fillColor: polygonColour,
                fillOpacity: 0.3,
                strokeColor: polygonColour,
                strokeWidth: 1.5,
                pointRadius: 5
            }/*,
            OpenLayers.Feature.Vector.style["default"]*/));
        return regionStyleMap;
    };

    // Create default style mapping for a user region on the drawing region page
    window.pos.create_user_region_style_map = function() {

        var regionStyleMap = new OpenLayers.StyleMap({
            "temporary": OpenLayers.Util.applyDefaults({
                fillOpacity: 0.3,
                fillColor: 'red',
                strokeColor: 'red',
                pointRadius: 5,
                strokeWidth: 1.5,
                strokeDashstyle: "dash"
            }, OpenLayers.Feature.Vector.style.temporary),
            "default": OpenLayers.Util.applyDefaults({
                fillOpacity: 0.3,
                pointRadius: 5,
                strokeWidth: 1.5,
                fillColor: '#BB8CF7',
                strokeColor: '#BB8CF7'
            }, OpenLayers.Feature.Vector.style['default']),
            "select": OpenLayers.Util.applyDefaults({
                fillOpacity: 0.3,
                pointRadius: 5,
                strokeWidth: 1.5,
                fillColor: 'red',
                strokeColor: 'red',
                strokeDashstyle: "dash"
            }, OpenLayers.Feature.Vector.style.select)
        });

        return regionStyleMap;
    };

    // Create lookup for stylings of POSs in the map views for different POS types
    // Extends the default pos style map
    window.pos.create_pos_colour_lookup = function() {
        address.posColourLookup = {
            "Park": {fillColor: "${fill_colour}", strokeColor: "${border_colour}"},
            "Natural": {fillColor: "#3B8300", strokeColor: "#3B8300"},
            "Residual Green Space": {fillColor: "#56B1CA", strokeColor: "#56B1CA"},
            "School Grounds": {fillColor: "#F6862A", strokeColor: "#F6862A"},
            "Club or Pay Facilities": {fillColor: "#8B73A9", strokeColor: "#8B73A9"}
        };
        return address.posColourLookup;
    };

    // Create style array for Google Streets base map
    window.pos.create_google_streets_styles = function() {
        var google_streets_styles =    [
            {
            featureType: "poi.park",
            stylers: [
                { hue: "#eeff00" },
                { saturation: -25 },
                { lightness: 41 }
            ]
            },{
            featureType: "poi.business",
            stylers: [
                { lightness: 36 },
                { hue: "#ffc300" }
                ]
            },{
            featureType: "road.arterial",
            stylers: [
                { lightness: 28 },
                { hue: "#ffcc00" }
            ]
            },{
            featureType: "poi.medical",
            stylers: [
                { hue: "#a200ff" },
                { lightness: 14 }
            ]
            },{
            featureType: "road.highway",
            stylers: [
            { hue: "#ffa200" },
            { lightness: 39 }
            ]
            }
        ];
        return google_streets_styles;
    };

    // Build the vector layers for the POS map
    window.pos.map.buildPOSVectors = function(json_list){
        var map = pos.map.base_map;
        var wgs84 = new OpenLayers.Projection("EPSG:4326");
        var displayBounds = new OpenLayers.Bounds(); // Set up map display boundaries

        // Remove all the existing features before adding new ones
        for (var i=0; i<address.polygonVectorsArr.length; ++i) {
            address.polygonVectorsArr[i].destroyFeatures();
        }

        // Begin adding POS polygon features
        for (var i=0; i<json_list.length; ++i) {
            //var polyGeometry = new OpenLayers.Geometry.fromWKT(json_list[i]['pos_wkt']);
            var polyGeometry = new OpenLayers.Geometry.fromWKT(json_list[i].pos_wkt);
            polyGeometry.transform(wgs84, map.getProjectionObject()); // make it Google Mercator
            var polyFeature;

            polyFeature = new OpenLayers.Feature.Vector(polyGeometry, {
                                    //pos_type_c: json_list[i]['pos_type_c'],
                                    pos_type_c: json_list[i].pos_type_c,
                                    //pos_pk: json_list[i]['pos_pk'],
                                    pos_pk: json_list[i].pos_pk,
                                    fill_colour: "#9BBC58",
                                    border_colour: "#8CAA4F" });

            if (i === 0) {
                // Extend the map display boundaries for this searched Park, other parts of the POS can remain outside the map view
                displayBounds.extend(polyGeometry.getBounds());

            }

            // Add feature to the correct layer in the array of layers
            var layerIndex;
            for (var j=0; j<address.types_list.length; ++j) {
                if (address.types_list[j].description === json_list[i].pos_type_c) {
                    layerIndex = j;
                    address.polygonVectorsArr[layerIndex].addFeatures(polyFeature);
                    // console.log(i + ", " + address.types_list[j].description);
                }
            }
        }
        // Lookup all the stylings for each POS type, and add to the styleMap
        address.posStyleMap.addUniqueValueRules("default", "pos_type_c", address.posColourLookup);

        // Add the search location's lat/long to the map
        var pointVector = new OpenLayers.Geometry.Point(address.lon, address.lat);
        pointVector.transform(wgs84, map.getProjectionObject()); // make it Google Mercator
        var pointFeature = new OpenLayers.Feature.Vector(pointVector);
        address.searchPointVector.addFeatures(pointFeature);
        // Add the point to the vectors array - OpenLayers bug with conflicting controls on multiple layers
        // Hence workaround by making the point part of the polygons array instead of a completely separate layer
        address.polygonVectorsArr[address.types_list.length] = address.searchPointVector; // i.e. index 5 is the 6th element

        // Add the polygon vector layers to the map
        for (i=0; i<=address.types_list.length; ++i) {
            map.addLayers([address.polygonVectorsArr[i]]);
        }

        // map.addLayers([address.searchedParkVector, address.polygonVector]);

        // Zoom to bounds of all Geometries
        map.zoomToExtent(displayBounds, true);
        map.zoomTo(map.getZoomForExtent(displayBounds));

        return displayBounds;
    };

    // Build the vector layers for the address map
    window.pos.map.buildAddressVectors = function(json_list){
        var map = pos.map.base_map;
        var wgs84 = new OpenLayers.Projection("EPSG:4326");
        var displayBounds = new OpenLayers.Bounds(); // Set up map display boundaries

        // Remove all the existing features before adding new ones
        for (var i=0; i<address.polygonVectorsArr.length; ++i) {
            address.polygonVectorsArr[i].destroyFeatures();
        }

        // Begin adding POS polygon features
        for(i=0; i<json_list.length; ++i) {
            var polyFeature;
            var polyGeometry = new OpenLayers.Geometry.fromWKT(json_list[i].pos_wkt);
            polyGeometry.transform(wgs84, map.getProjectionObject()); // make the geometry in Google Mercator
            if (i < address.num_parks) {
                // Extend the map display boundaries for the nearest 'X' Parks, others can remain outside the map view
                displayBounds.extend(polyGeometry.getBounds());
                polyFeature = new OpenLayers.Feature.Vector(polyGeometry, {
                    //pos_type_c: json_list[i]['pos_type_c'],
                    //pos_pk: json_list[i]['pos_pk'],
                    //park_name: json_list[i]['name'],
                    pos_type_c: json_list[i].pos_type_c,
                    pos_pk: json_list[i].pos_pk,
                    park_name: json_list[i].name,
                    //fill_colour: "green",
                    //border_colour: "green" });
                    fill_colour: "#9BBC58",
                    border_colour: "#8CAA4F"
                });
            }
            else {
                polyFeature = new OpenLayers.Feature.Vector(polyGeometry, {
                    //pos_type_c: json_list[i]['pos_type_c'],
                    //pos_pk: json_list[i]['pos_pk'],
                    pos_type_c: json_list[i].pos_type_c,
                    pos_pk: json_list[i].pos_pk,
                    park_name: '',
                    //fill_colour: "green",
                    //border_colour: "green" });
                    fill_colour: "#9BBC58",
                    border_colour: "#8CAA4F"
                });
            }
            // Add feature to the correct layer in the array of layers
            for (var j=0; j<address.types_list.length; ++j) {
                if (address.types_list[j].description === json_list[i].pos_type_c) {
                    var layerIndex = j;
                    address.polygonVectorsArr[layerIndex].addFeatures(polyFeature);
                    //console.log(i + ", " + address.types_list[j].description);
                }
            }
            // Create a popup for the feature
    /*        if (json_list[i].name == '') {
                    popupText = json_list[i].pos_type_c;
            }
            else {
                    popupText = json_list[i].name;
            }
            pos.createPopup("POS Feature Popup", popupText, polyFeature);
    */

            if (json_list[i].adj_bush === 1) {
                var popupText = "Contains or adjacent<br>to Bush Forever";
                pos.createPopup("POS Feature Popup", popupText, polyFeature);
            }
        }

        // Lookup all the stylings for each POS type, and add to the styleMap
        address.posStyleMap.addUniqueValueRules("default", "pos_type_c", address.posColourLookup);

        // Add the search location's lat/long to the map
        var pointVector = new OpenLayers.Geometry.Point(address.lon, address.lat);
        pointVector.transform(wgs84, map.getProjectionObject()); // make it Google Mercator
        var pointFeature = new OpenLayers.Feature.Vector(pointVector);
        address.searchPointVector.addFeatures(pointFeature);
        // Add the point to the vectors array - OpenLayers bug with conflicting controls on multiple layers
        // Hence workaround by making the point part of the polygons array instead of a completely separate layer
        address.polygonVectorsArr[address.types_list.length] = address.searchPointVector; // i.e. index 5 is the 6th element

        // Add the polygon vector layers to the map
    //    map.addLayers([polygonVectorsArr[address.types_list.length]]); // Make address marker the 1st in LayerSwitcher list by adding it 1st
        for (i=0; i<=address.types_list.length; ++i) {
            map.addLayers([address.polygonVectorsArr[i]]);
        }

        return displayBounds;
    };

    // Control the switch between vector and WMS POS layers as map is zoomed
    window.pos.map.onZoomMap = function(event) {
        var map = pos.map.base_map;
        var WMSlayers = map.pos.layersWMS;
        var oldScale = map.pos.scale;
        var newScale = map.getScale();
        var layerVisibility = [];

        // Abort old ajax requests
        if (pos.map.ajaxRequest !== undefined) {
           pos.map.ajaxRequest.abort();
           pos.map.ajaxRequest = undefined;
        }

        // Check if the scale threshold has been crossed, going down or up
        if ( ((oldScale > address.scaleSwitch) && (newScale < address.scaleSwitch)) ||
             ((oldScale < address.scaleSwitch) && (newScale > address.scaleSwitch)) ) {

            var viz = {};
            var i, j;
            if (newScale < address.scaleSwitch){

                // Set the
                //pos.map.ajaxRequest = undefined;

                // Remove the WMS Layers
                for (i=0; i<WMSlayers.length; ++i) {
                    viz[WMSlayers[i].name] = WMSlayers[i].visibility;
                    map.removeLayer(WMSlayers[i]);
                }

                // Add the vector layers
                map.addLayers(address.polygonVectorsArr);

                // Set the correct visibility
                for (j=0; j<layerVisibility.length; ++j) {
                    if(layerVisibility[j][0] === address.polygonVectorsArr[j].name){
                        address.polygonVectorsArr[j].setVisibility(viz[address.polygonVectorsArr[j].name]);
                    }
                }
            } else {

                // Remove the vector layers
                for (i=0; i<=address.types_list.length; ++i) {
                    if(address.polygonVectorsArr[i].name !== "Your Location"){
                        viz[address.polygonVectorsArr[i].name] = address.polygonVectorsArr[i].visibility;
                        map.removeLayer(address.polygonVectorsArr[i]);
                    }
                }

                // Add the WMS layers
                map.addLayers(WMSlayers);

                // Set the correct visibility
                for (j=0; j<map.getNumLayers(); ++j) {
                    if (map.layers[j].CLASS_NAME === "OpenLayers.Layer.WMS"){
                        if ((map.layers[j].name !== "Suburbs") && (map.layers[j].name !== "Local Government Areas")) {
                            map.layers[j].setVisibility(viz[map.layers[j].name]);
                        }

                    }
                }

                // Remove any open popups
                for (i=0; i<map.popups.length; ++i) {
                    map.removePopup(map.popups[i]);
                }
            }

            // Move the address point to the bottom of the layer switcher control
            var controlLayers = (map.getControlsByClass("OpenLayers.Control.LayerSwitcher")[0].layerStates.length) - 1;
            map.setLayerIndex(address.searchPointVector, controlLayers);
        }

        // console.log(address.searchPointVector);
        // console.log(map.pos.extent);

        // If the extent hasn't been set before, calculate it
        if (map.pos.extent === undefined){
            map.pos.extent = pos.map.calculateLargeExtent(map.getExtent());
        }

        // If the map view has zoomed outside the extent of the existing vector features, request a new set
        if (pos.map.checkVectorRecalc() === true) {
            pos.map.requestFeatures(pos.map.calculateLargeExtent(map.getExtent()));
        }
    };

    // At the start of a pan or zoom - grab the scale
    window.pos.map.onMoveStart = function(event) {
        var map = pos.map.base_map;

        // Store the original zoom in the map object
        map.pos.scale = map.getScale();
    };

    // When the map is panned check if if we need to grab some more vector features
    window.pos.map.onMoveEnd = function(event) {
        var map = pos.map.base_map;

        // Check if the event is a pan
        if (map.pos.scale === map.getScale()){
            // Abort old ajax requests
            if (pos.map.ajaxRequest !== undefined) {
                pos.map.ajaxRequest.abort();
                pos.map.ajaxRequest = undefined;
            }

            // If the extent hasn't been set before, calculate it
            if (map.pos.extent === undefined) {
                map.pos.extent = pos.map.calculateLargeExtent(map.getExtent());
            }

            // If the map view has panned outside the extent of the existing vector features, request a new set
            if (pos.map.checkVectorRecalc()){
                pos.map.requestFeatures(pos.map.calculateLargeExtent(map.getExtent()));
            }
        }
    };

    // Calculate a larger extent based on the current extent
    window.pos.map.calculateLargeExtent = function(currentExtent) {
        var map = pos.map.base_map;
        var newExtent;

        // Set the extent multiplier value - This is used to create a larger extent to use to grab vector features
        var extentMultiplier = 2;

        // If the multiplier is greater than 1 calculate it, otherwise set it to the current extent
        if (extentMultiplier > 1 && map.getScale() < address.scaleSwitch / 2) {
            var extentWidth = currentExtent.right - currentExtent.left;
            var extentHeight = currentExtent.top - currentExtent.bottom;
            var widthChange = ((extentWidth * extentMultiplier) - extentWidth) / 2;
            var heightChange = ((extentHeight * extentMultiplier) - extentHeight) / 2;
            newExtent = new OpenLayers.Bounds(
                currentExtent.left - widthChange,
                currentExtent.bottom - heightChange,
                currentExtent.right + widthChange,
                currentExtent.top + heightChange
            );
        }
        else {
            newExtent = currentExtent;
        }

        return newExtent;
    };

    // Check if we need to request a new set of vector features
    window.pos.map.checkVectorRecalc = function() {
        var map = pos.map.base_map;

        return map.pos.extent.containsBounds(map.getExtent()) === false && map.getScale() < address.scaleSwitch;
    };

    // Request a new set of vector features
    window.pos.map.requestFeatures = function(extent){
        var map = pos.map.base_map;
        map.pos.extent = extent;

        // Create the wkt string
        var wkt = new OpenLayers.Format.WKT();
        var wkt_str = wkt.extractGeometry(map.pos.extent.toGeometry());

        // Request features from the server
        pos.map.ajaxRequest = jQuery.getJSON('/cbeh/pos/ajax_bbox_pos/', {
        'bbox': wkt_str,
        //'srid': 900913
        'srid': map.getProjection().split(":")[1]
        }, function(data) {
            if(address.functionCalled === "Address"){
                pos.map.buildAddressVectors(data);
            }
            else if (address.functionCalled === "POS"){
                pos.map.buildAddressVectors(data);
            }
        }
        );
    };

    // Create the WMS POS layers
    window.pos.map.createWMSPOSLayers = function() {
        // Grab GeoServer WMS url
        var WMS_URL = pos.map.geoserverURL;
        var WMS_Options;
        var resultArray;
        //var WMS_URL = 'http://192.168.2.211:8080/geoserver/UWA-POS/wms';

        // Set the layer options
        // if(address.functionCalled === "POS" || address.functionCalled === "Region"){
        if(address.functionCalled === "Region"){
            WMS_Options = {displayOutsideMaxExtent: true,
                isBaseLayer: false,
                displayInLayerSwitcher: true,
                yx : {'EPSG:28350' : false}};

            // Create the layer
            var pos_pos = new OpenLayers.Layer.WMS("Public Open Spaces", WMS_URL,{LAYERS: 'UWA-POS:pos_pos',transparent: true},WMS_Options);

            // Create a layer array and return it
            resultArray = [pos_pos];

        }
        else if (address.functionCalled === "Address" || address.functionCalled === "POS"){
            WMS_Options = {displayOutsideMaxExtent: true,
                isBaseLayer: false,
                maxScale: address.scaleSwitch,
                units: address.scaleUnits,
                visibility: false,
                yx : {'EPSG:28350' : false}};

            // Create the layers
            var pos_club = new OpenLayers.Layer.WMS("Club or Pay Facilities", WMS_URL,{LAYERS: 'UWA-POS:pos_pos_club',transparent: true},WMS_Options);
            var pos_green = new OpenLayers.Layer.WMS("Residual Green Space", WMS_URL,{LAYERS: 'UWA-POS:pos_pos_green',transparent: true},WMS_Options);
            var pos_natural = new OpenLayers.Layer.WMS("Natural", WMS_URL,{LAYERS: 'UWA-POS:pos_pos_natural',transparent: true},WMS_Options);
            var pos_school = new OpenLayers.Layer.WMS("School Grounds", WMS_URL,{LAYERS: 'UWA-POS:pos_pos_school',transparent: true},WMS_Options);
            var pos_park = new OpenLayers.Layer.WMS("Park", WMS_URL,{LAYERS: 'UWA-POS:pos_pos_park',transparent: true},WMS_Options);

            // Create a layers array and return it
            resultArray = [pos_park, pos_natural, pos_school, pos_club, pos_green];
        }

        return resultArray;
    };

    // Create the WMS LGA layer
    window.pos.map.createWMSLGALayer = function() {
        // Grab GeoServer WMS url
        var WMS_URL = pos.map.geoserverURL;
        var WMS_Options;
        var resultArray;

        // Set the layer options
        WMS_Options = {displayOutsideMaxExtent: true,
            isBaseLayer: false,
            displayInLayerSwitcher: true,
            visibility: false,
            yx : {'EPSG:28350' : false}};

        // Create the layer
        var pos_region_lga = new OpenLayers.Layer.WMS("Local Government Areas", WMS_URL,{LAYERS: 'UWA-POS:pos_region_lga',transparent: true},WMS_Options);

        // Create a layer array and return it
        return pos_region_lga;
    };

    // Create the WMS Suburb layer
    window.pos.map.createWMSSuburbLayer = function() {
        // Grab GeoServer WMS url
        var WMS_URL = pos.map.geoserverURL;
        var WMS_Options;
        var resultArray;

        // Set the layer options
        WMS_Options = {displayOutsideMaxExtent: true,
            isBaseLayer: false,
            displayInLayerSwitcher: true,
            visibility: false,
            yx : {'EPSG:28350' : false}};

        // Create the layer
        var pos_region_suburb = new OpenLayers.Layer.WMS("Suburbs", WMS_URL,{LAYERS: 'UWA-POS:pos_region_suburb',transparent: true},WMS_Options);

        // Create a layer array and return it
        return pos_region_suburb;
    };

}());
